"""Resolve um DashboardSpec em DashboardResult. O tenant não entra no spec."""

from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel

from logidash.metrics.contexto_tenant import validar_spec
from logidash.metrics.erros import ConsultaInvalida, KpiDesconhecido
from logidash.metrics.modelos import ResultadoKpi
from logidash.metrics.motor_kpi import MotorKpi

_FONTE_ID = "embarques_demonstracao"
_TIPOS_WIDGET = frozenset({"kpi_card", "barra_horizontal"})
_DEFINICOES = Path(__file__).resolve().parents[1] / "metrics" / "definitions"


class FonteSpec(BaseModel):
    source_id: str
    modo: str


class FiltroSpec(BaseModel):
    campo: str
    operador: str
    valor: list[str]


class WidgetSpec(BaseModel):
    tipo: str
    kpi: str
    largura: int
    dimensao: str | None = None
    ordenar: str | None = None
    limite: int | None = None


class DashboardSpec(BaseModel):
    id: str
    titulo: str
    fonte: FonteSpec
    filtros: list[FiltroSpec]
    layout: list[WidgetSpec]


class SerieDashboard(BaseModel):
    nome: str
    rotulo: str
    valor: str | None
    unidade: str


class WidgetDashboard(BaseModel):
    tipo: str
    rotulo: str
    unidade: str
    formatacao: str
    meta: str | None
    series: list[SerieDashboard]


class RejeicaoDashboard(BaseModel):
    indice_linha: int
    shipment_id: str | None
    regra: str
    campo: str | None
    mensagem: str


class DashboardResult(BaseModel):
    id: str
    titulo: str
    widgets: list[WidgetDashboard]
    rejeicoes: list[RejeicaoDashboard]


def spec_painel_otif() -> DashboardSpec:
    return DashboardSpec.model_validate(
        {
            "id": "painel_otif",
            "titulo": "Painel de entregas",
            "fonte": {"source_id": _FONTE_ID, "modo": "MATERIALIZE"},
            "filtros": [
                {
                    "campo": "data_prometida_original",
                    "operador": "entre",
                    "valor": ["2026-01-01", "2026-01-31"],
                }
            ],
            "layout": [
                {"tipo": "kpi_card", "kpi": "otif", "largura": 6},
                {
                    "tipo": "barra_horizontal",
                    "kpi": "otif",
                    "dimensao": "carrier_id",
                    "ordenar": "asc",
                    "limite": 10,
                    "largura": 6,
                },
            ],
        }
    )


def resolver_spec(
    motor: MotorKpi,
    token: str,
    corpo: object,
    embarques: Sequence[Mapping[str, object]],
) -> DashboardResult:
    validar_spec(corpo)
    if not isinstance(corpo, Mapping):
        raise ConsultaInvalida("A consulta precisa ser um registro.")
    spec = _ler_spec(corpo)
    inicio, fim = _periodo(spec)
    consulta_base = {"kpi": "otif", "parametros": {"inicio": inicio, "fim": fim}}
    total: ResultadoKpi | None = None
    por_transportadora: ResultadoKpi | None = None
    widgets: list[WidgetDashboard] = []
    for item in spec["layout"]:
        _exigir_kpi_otif(motor, token, item, embarques, inicio, fim)
        if item["tipo"] == "kpi_card":
            if total is None:
                total = motor.executar(token=token, consulta=consulta_base, embarques=embarques)
            widgets.append(_widget_card(total))
        else:
            if por_transportadora is None:
                por_transportadora = motor.executar(
                    token=token,
                    consulta={**consulta_base, "agregar_por": "carrier_id"},
                    embarques=embarques,
                )
            widgets.append(_widget_barra(por_transportadora, item))
    if total is None and por_transportadora is None:
        raise ConsultaInvalida("O layout precisa de ao menos um widget.")
    relatorio = (total or por_transportadora).rejeicoes
    return DashboardResult(
        id=spec["id"],
        titulo=spec["titulo"],
        widgets=widgets,
        rejeicoes=[
            RejeicaoDashboard(
                indice_linha=item.indice_linha,
                shipment_id=item.shipment_id,
                regra=item.regra,
                campo=item.campo,
                mensagem=item.mensagem,
            )
            for item in relatorio.violacoes
        ],
    )


def _ler_spec(corpo: Mapping[str, object]) -> dict[str, object]:
    identificador = corpo.get("id")
    titulo = corpo.get("titulo")
    if type(identificador) is not str or identificador == "" or type(titulo) is not str or titulo == "":
        raise ConsultaInvalida("O spec precisa de id e titulo.")
    fonte = corpo.get("fonte")
    if not isinstance(fonte, Mapping):
        raise ConsultaInvalida("O spec precisa da fonte.")
    if fonte.get("source_id") != _FONTE_ID or fonte.get("modo") != "MATERIALIZE":
        raise ConsultaInvalida("A fonte deste recorte é embarques_demonstracao em modo MATERIALIZE.")
    layout = corpo.get("layout")
    if not isinstance(layout, list) or not layout:
        raise ConsultaInvalida("O layout precisa de ao menos um widget.")
    itens: list[dict[str, object]] = []
    for bruto in layout:
        if not isinstance(bruto, Mapping):
            raise ConsultaInvalida("Cada widget do layout precisa ser um registro.")
        tipo = bruto.get("tipo")
        kpi = bruto.get("kpi")
        if tipo not in _TIPOS_WIDGET or type(kpi) is not str:
            raise ConsultaInvalida("O tipo de widget não é aceito neste recorte.")
        item: dict[str, object] = {"tipo": tipo, "kpi": kpi}
        if tipo == "barra_horizontal":
            if bruto.get("dimensao") != "carrier_id":
                raise ConsultaInvalida("A dimensão precisa ser o campo canônico carrier_id.")
            ordenar = bruto.get("ordenar", "asc")
            if ordenar not in {"asc", "desc"}:
                raise ConsultaInvalida("A ordenação do widget é asc ou desc.")
            limite = bruto.get("limite", 10)
            if type(limite) is not int or isinstance(limite, bool) or limite < 1:
                raise ConsultaInvalida("O limite do widget precisa ser um inteiro positivo.")
            item["ordenar"] = ordenar
            item["limite"] = limite
        itens.append(item)
    return {"id": identificador, "titulo": titulo, "layout": itens, "filtros": corpo.get("filtros")}


def _periodo(spec: Mapping[str, object]) -> tuple[date, date]:
    filtros = spec.get("filtros")
    if not isinstance(filtros, list):
        raise ConsultaInvalida("O spec precisa filtrar data_prometida_original.")
    escolhido = None
    for filtro in filtros:
        if not isinstance(filtro, Mapping):
            raise ConsultaInvalida("O spec precisa filtrar data_prometida_original.")
        if filtro.get("campo") != "data_prometida_original" or filtro.get("operador") != "entre":
            raise ConsultaInvalida(
                "O filtro do período usa data_prometida_original entre o início e o fim."
            )
        if escolhido is not None:
            raise ConsultaInvalida("O spec precisa de um único filtro de período.")
        escolhido = filtro
    if escolhido is None:
        raise ConsultaInvalida("O spec precisa filtrar data_prometida_original.")
    valor = escolhido.get("valor")
    if not isinstance(valor, list) or len(valor) != 2:
        raise ConsultaInvalida("O filtro entre precisa de duas datas.")
    return _data(valor[0]), _data(valor[1])


def _data(valor: object) -> date:
    if type(valor) is not str:
        raise ConsultaInvalida("O parâmetro do período deve ser uma data.")
    try:
        return date.fromisoformat(valor)
    except ValueError as exc:
        raise ConsultaInvalida("O parâmetro do período deve ser uma data.") from exc


def _exigir_kpi_otif(
    motor: MotorKpi,
    token: str,
    item: Mapping[str, object],
    embarques: Sequence[Mapping[str, object]],
    inicio: date,
    fim: date,
) -> None:
    kpi = item["kpi"]
    if kpi == "otif":
        return
    motor.executar(
        token=token,
        consulta={"kpi": kpi, "parametros": {"inicio": inicio, "fim": fim}},
        embarques=embarques,
    )
    raise KpiDesconhecido("O KPI informado não está definido.")


def _widget_card(resultado: ResultadoKpi) -> WidgetDashboard:
    rotulo, unidade, meta = _metadados(resultado.kpi)
    return WidgetDashboard(
        tipo="kpi_card",
        rotulo=rotulo,
        unidade=unidade,
        formatacao=unidade,
        meta=meta,
        series=[
            SerieDashboard(nome="valor", rotulo="Valor", valor=_texto(resultado.valor), unidade=unidade),
            SerieDashboard(
                nome="numerador",
                rotulo="Numerador",
                valor=str(resultado.numerador),
                unidade="embarque",
            ),
            SerieDashboard(
                nome="denominador",
                rotulo="Denominador",
                valor=str(resultado.denominador),
                unidade="embarque",
            ),
        ],
    )


def _widget_barra(resultado: ResultadoKpi, item: Mapping[str, object]) -> WidgetDashboard:
    rotulo, unidade, meta = _metadados(resultado.kpi)
    grupos = list(resultado.grupos)
    if item.get("ordenar") == "desc":
        grupos.reverse()
    limite = item.get("limite")
    if type(limite) is int and not isinstance(limite, bool):
        grupos = grupos[:limite]
    return WidgetDashboard(
        tipo="barra_horizontal",
        rotulo=rotulo,
        unidade=unidade,
        formatacao=unidade,
        meta=meta,
        series=[
            SerieDashboard(
                nome=grupo.chave or "",
                rotulo=grupo.chave or "Sem identificador",
                valor=_texto(grupo.valor),
                unidade=unidade,
            )
            for grupo in grupos
        ],
    )


def _metadados(kpi_id: str) -> tuple[str, str, str | None]:
    caminho = _DEFINICOES / f"{kpi_id}.yaml"
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        return kpi_id, "fracao", None
    nome = dados.get("nome")
    unidade = dados.get("unidade")
    meta = dados.get("meta_padrao")
    return (
        nome if isinstance(nome, str) and nome else kpi_id,
        unidade if isinstance(unidade, str) and unidade else "fracao",
        meta if isinstance(meta, str) and meta else None,
    )


def _texto(valor: object) -> str | None:
    if valor is None:
        return None
    return str(valor)
