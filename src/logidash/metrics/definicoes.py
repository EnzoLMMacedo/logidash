"""Carrega a definição versionada de um KPI. A fórmula não é reescrita aqui."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from logidash.metrics.erros import ConsultaInvalida, KpiDesconhecido

_DIRETORIO = Path(__file__).resolve().parent / "definitions"
_ID_KPI = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class DefinicaoKpi:
    id: str
    agregacao: str
    tabela: str
    sql: str


def carregar_definicao(kpi_id: str) -> DefinicaoKpi:
    if type(kpi_id) is not str or _ID_KPI.fullmatch(kpi_id) is None:
        raise KpiDesconhecido("O KPI informado não está definido.")
    caminho = _DIRETORIO / f"{kpi_id}.yaml"
    if not caminho.is_file():
        raise KpiDesconhecido("O KPI informado não está definido.")
    carregado = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    if not isinstance(carregado, dict):
        raise KpiDesconhecido("O KPI informado não está definido.")
    if carregado.get("id") != kpi_id:
        raise KpiDesconhecido("O KPI informado não está definido.")
    agregacao = carregado.get("agregacao")
    if agregacao != "razao_de_somas":
        raise ConsultaInvalida("O KPI informado não é da classe razao_de_somas.")
    if carregado.get("tabela") != "fact_shipment":
        raise ConsultaInvalida("O KPI informado não lê fact_shipment.")
    sql = carregado.get("sql")
    if type(sql) is not str or sql.strip() == "":
        raise KpiDesconhecido("O KPI informado não está definido.")
    return DefinicaoKpi(
        id=kpi_id,
        agregacao=agregacao,
        tabela="fact_shipment",
        sql=sql,
    )
