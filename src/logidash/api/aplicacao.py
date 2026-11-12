"""FastAPI que expõe o motor. O tenant sai do token, nunca do corpo."""

from collections.abc import Mapping
from datetime import date
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from json import JSONDecodeError

from logidash.api.fixtures_painel import EMBARQUES, TOKENS_DEMONSTRACAO
from logidash.api.gerador import DashboardResult, DashboardSpec, resolver_spec, spec_painel_otif
from logidash.metrics.contexto_tenant import ResolvedorDeTokenEmMemoria
from logidash.metrics.erros import (
    ConsultaInvalida,
    ErroLogidash,
    KpiDesconhecido,
    SpecRejeitado,
    TokenInvalido,
)
from logidash.metrics.modelos import ResultadoKpi
from logidash.metrics.motor_kpi import MotorKpi

_DIRETORIO_DEFINICOES = Path(__file__).resolve().parents[1] / "metrics" / "definitions"


class SerieResposta(BaseModel):
    nome: str
    valor: int


class RejeicaoResposta(BaseModel):
    indice_linha: int
    shipment_id: str | None
    regra: str
    campo: str | None
    mensagem: str


class PainelResposta(BaseModel):
    rotulo: str
    valor: str | None
    unidade: str
    numerador: int
    denominador: int
    agregacao: str
    periodo_inicio: str
    periodo_fim: str
    series: list[SerieResposta]
    rejeicoes: list[RejeicaoResposta]


def criar_aplicacao() -> FastAPI:
    aplicacao = FastAPI(title="LogiDash", version="0.1.0")
    motor = MotorKpi(ResolvedorDeTokenEmMemoria(TOKENS_DEMONSTRACAO))

    @aplicacao.get("/api/saude")
    def saude() -> dict[str, str]:
        return {"situacao": "no_ar"}

    @aplicacao.post("/api/painel/otif", response_model=PainelResposta)
    async def painel_otif(requisicao: Request) -> PainelResposta:
        token = _token_do_cabecalho(requisicao.headers.get("authorization"))
        corpo = await requisicao.json()
        if not isinstance(corpo, dict):
            raise ConsultaInvalida("A consulta precisa ser um registro.")
        consulta = _preparar_consulta(corpo)
        resultado = motor.executar(token=token, consulta=consulta, embarques=EMBARQUES)
        return _para_resposta(resultado, consulta)

    @aplicacao.get("/api/paineis/spec", response_model=DashboardSpec)
    def spec_do_painel() -> DashboardSpec:
        return spec_painel_otif()

    @aplicacao.post("/api/paineis/resultado", response_model=DashboardResult)
    async def resultado_do_painel(requisicao: Request) -> DashboardResult:
        token = _token_do_cabecalho(requisicao.headers.get("authorization"))
        try:
            corpo = await requisicao.json()
        except JSONDecodeError as exc:
            raise ConsultaInvalida("A consulta precisa ser um registro.") from exc
        return resolver_spec(motor, token, corpo, EMBARQUES)

    @aplicacao.exception_handler(ErroLogidash)
    async def erro_de_dominio(_requisicao: Request, exc: ErroLogidash) -> JSONResponse:
        return JSONResponse(status_code=_status_erro(exc), content={"detail": str(exc)})

    return aplicacao


def _token_do_cabecalho(autorizacao: str | None) -> str:
    if not autorizacao or not autorizacao.startswith("Bearer "):
        raise TokenInvalido("Token ausente. Envie o cabeçalho Authorization: Bearer.")
    token = autorizacao.removeprefix("Bearer ").strip()
    if token == "":
        raise TokenInvalido("Token ausente. Envie o cabeçalho Authorization: Bearer.")
    return token


def _preparar_consulta(corpo: Mapping[str, object]) -> dict[str, object]:
    consulta = dict(corpo)
    parametros = consulta.get("parametros")
    if isinstance(parametros, Mapping):
        convertidos = dict(parametros)
        for nome in ("inicio", "fim"):
            valor = convertidos.get(nome)
            if isinstance(valor, str):
                convertidos[nome] = _data_iso(nome, valor)
        consulta["parametros"] = convertidos
    return consulta


def _data_iso(nome: str, valor: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError as exc:
        raise ConsultaInvalida(f"O parâmetro {nome} deve ser uma data.") from exc


def _para_resposta(resultado: ResultadoKpi, consulta: Mapping[str, object]) -> PainelResposta:
    parametros = consulta.get("parametros")
    inicio = fim = ""
    if isinstance(parametros, Mapping):
        inicio_valor = parametros.get("inicio")
        fim_valor = parametros.get("fim")
        if isinstance(inicio_valor, date):
            inicio = inicio_valor.isoformat()
        if isinstance(fim_valor, date):
            fim = fim_valor.isoformat()
    rotulo, unidade = _rotulo_e_unidade(resultado.kpi)
    series: list[SerieResposta] = []
    if resultado.denominador > 0:
        series = [
            SerieResposta(nome="Numerador", valor=resultado.numerador),
            SerieResposta(
                nome="Restante do denominador",
                valor=resultado.denominador - resultado.numerador,
            ),
        ]
    return PainelResposta(
        rotulo=rotulo,
        valor=None if resultado.valor is None else str(resultado.valor),
        unidade=unidade,
        numerador=resultado.numerador,
        denominador=resultado.denominador,
        agregacao=resultado.agregacao,
        periodo_inicio=inicio,
        periodo_fim=fim,
        series=series,
        rejeicoes=[
            RejeicaoResposta(
                indice_linha=item.indice_linha,
                shipment_id=item.shipment_id,
                regra=item.regra,
                campo=item.campo,
                mensagem=item.mensagem,
            )
            for item in resultado.rejeicoes.violacoes
        ],
    )


def _rotulo_e_unidade(kpi_id: str) -> tuple[str, str]:
    caminho = _DIRETORIO_DEFINICOES / f"{kpi_id}.yaml"
    if not caminho.is_file():
        return kpi_id, "fracao"
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        return kpi_id, "fracao"
    nome = dados.get("nome")
    unidade = dados.get("unidade")
    return (
        nome if isinstance(nome, str) and nome else kpi_id,
        unidade if isinstance(unidade, str) and unidade else "fracao",
    )


def _status_erro(exc: ErroLogidash) -> int:
    if isinstance(exc, TokenInvalido):
        return 401
    if isinstance(exc, KpiDesconhecido):
        return 404
    if isinstance(exc, (SpecRejeitado, ConsultaInvalida)):
        return 422
    return 500


app = criar_aplicacao()
