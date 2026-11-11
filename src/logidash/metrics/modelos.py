"""Resultados do motor. O valor do KPI é fração decimal, sem formatação."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ViolacaoContrato:
    indice_linha: int
    shipment_id: str | None
    regra: str
    campo: str | None
    mensagem: str


@dataclass(frozen=True)
class RelatorioRejeicao:
    violacoes: tuple[ViolacaoContrato, ...]

    @property
    def quantidade_linhas(self) -> int:
        return len({violacao.indice_linha for violacao in self.violacoes})


@dataclass(frozen=True)
class GrupoKpi:
    dimensao: str
    chave: str | None
    valor: Decimal | None
    numerador: int
    denominador: int


@dataclass(frozen=True)
class ResultadoKpi:
    kpi: str
    valor: Decimal | None
    numerador: int
    denominador: int
    agregacao: str
    grupos: tuple[GrupoKpi, ...]
    rejeicoes: RelatorioRejeicao
