"""Release: parse em AST, allowlist, bloqueio de DDL/DML."""

import pytest

from logidash.metrics.erros import SqlRejeitada
from logidash.metrics.executor_duckdb import executar_consulta
from logidash.metrics.guardiao_sql import analisar_sql, verificar_consulta, verificar_definicao

_DEFINICAO = """
SELECT
    SUM(CASE WHEN s.data_entrega IS NOT NULL THEN 1 ELSE 0 END)::DECIMAL
        / NULLIF(COUNT(*), 0) AS otif
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
"""


def _definir(sql: str) -> None:
    verificar_definicao(analisar_sql(sql, dialeto=None))


def _rejeitar(sql: str) -> None:
    dialeto = None if ";" in sql else "duckdb"
    arvore = analisar_sql(sql, dialeto=dialeto)
    if type(arvore).__name__ != "Select":
        verificar_definicao(arvore)
        return
    try:
        verificar_definicao(arvore)
    except SqlRejeitada as exc:
        if "tenant" not in str(exc):
            raise
        verificar_consulta(arvore)


@pytest.mark.parametrize(
    ("sql", "trecho"),
    [
        ("DROP TABLE fact_shipment", "DDL"),
        ("CREATE TABLE x (a INT)", "DDL"),
        ("ALTER TABLE fact_shipment ADD COLUMN x INT", "DDL"),
        ("TRUNCATE TABLE fact_shipment", "DDL"),
        ("DELETE FROM fact_shipment", "DML"),
        ("INSERT INTO fact_shipment VALUES (1)", "DML"),
        ("UPDATE fact_shipment SET status_final = 'ENTREGUE'", "DML"),
        ("COPY fact_shipment TO 'x'", "DML"),
        ("SELECT 1; DROP TABLE fact_shipment", "apenas um comando"),
        ("SELECT read_parquet('x')", "allowlist"),
        ("SELECT * FROM read_csv_auto('x')", "allowlist"),
        ("SELECT getenv('PATH')", "allowlist"),
        ("SELECT current_setting('memory_limit')", "allowlist"),
        ("ATTACH 'x.db' AS outro", "leitura"),
        ("INSTALL httpfs", "leitura"),
        ("PRAGMA version", "leitura"),
        ("SET memory_limit='1MB'", "leitura"),
        ("SELECT * FROM fact_shipment UNION ALL SELECT * FROM outro", "leitura"),
        (
            "WITH t AS (SELECT * FROM fact_shipment) SELECT * FROM t",
            "não permitida|allowlist",
        ),
    ],
)
def test_comandos_perigosos_sao_bloqueados(sql: str, trecho: str) -> None:
    with pytest.raises(SqlRejeitada, match=trecho):
        _rejeitar(sql)


def test_or_nao_passa_na_allowlist() -> None:
    sql = _DEFINICAO.replace(
        "WHERE s.data_prometida_original BETWEEN :inicio AND :fim",
        "WHERE s.data_prometida_original BETWEEN :inicio AND :fim OR 1 = 1",
    )
    with pytest.raises(SqlRejeitada, match="allowlist"):
        _definir(sql)


def test_definicao_nao_pode_filtrar_tenant() -> None:
    sql = """
    SELECT SUM(1)::DECIMAL / NULLIF(COUNT(*), 0) AS otif
    FROM fact_shipment s
    WHERE s.tenant_id = 'outro'
      AND s.data_prometida_original BETWEEN :inicio AND :fim
    """
    with pytest.raises(SqlRejeitada, match="tenant_id"):
        _definir(sql)


def test_executor_bloqueia_dml_antes_de_rodar() -> None:
    with pytest.raises(SqlRejeitada, match="DML"):
        executar_consulta("DELETE FROM fact_shipment", {}, [])
