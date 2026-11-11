"""A fórmula executada é a do dicionário, não uma reescrita."""

from pathlib import Path

from logidash.metrics.definicoes import carregar_definicao
from logidash.metrics.erros import KpiDesconhecido

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _sql_otif_do_dicionario(texto: str) -> str:
    inicio = texto.index("### `otif`")
    fim = texto.index("### `otd`", inicio)
    trecho = texto[inicio:fim]
    abertura = trecho.index("```sql\n") + len("```sql\n")
    fechamento = trecho.index("\n```", abertura)
    return trecho[abertura:fechamento].strip()


def test_sql_de_otif_e_a_do_dicionario() -> None:
    dicionario = (RAIZ / "docs" / "kpis.md").read_text(encoding="utf-8")
    definicao = carregar_definicao("otif")
    sql = definicao.sql.strip()
    assert sql == _sql_otif_do_dicionario(dicionario)
    assert "data_prometida_original BETWEEN :inicio AND :fim" in sql
    assert "data_entrega BETWEEN" not in sql
    assert definicao.agregacao == "razao_de_somas"
    assert definicao.tabela == "fact_shipment"


@pytest.mark.parametrize("kpi_id", ["ocupacao_veiculo", "giro_estoque", "otd", "../otif"])
def test_kpi_fora_do_recorte_nao_existe(kpi_id: str) -> None:
    with pytest.raises(KpiDesconhecido):
        carregar_definicao(kpi_id)
