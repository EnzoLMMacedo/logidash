"""FastAPI que expõe o motor. O tenant sai do token, nunca do corpo."""

from json import JSONDecodeError

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
from logidash.metrics.motor_kpi import MotorKpi


def criar_aplicacao() -> FastAPI:
    aplicacao = FastAPI(title="LogiDash", version="0.1.0")
    motor = MotorKpi(ResolvedorDeTokenEmMemoria(TOKENS_DEMONSTRACAO))

    @aplicacao.get("/api/saude")
    def saude() -> dict[str, str]:
        return {"situacao": "no_ar"}

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


def _status_erro(exc: ErroLogidash) -> int:
    if isinstance(exc, TokenInvalido):
        return 401
    if isinstance(exc, KpiDesconhecido):
        return 404
    if isinstance(exc, (SpecRejeitado, ConsultaInvalida)):
        return 422
    return 500


app = criar_aplicacao()
