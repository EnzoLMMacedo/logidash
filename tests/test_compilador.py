"""A SQL compilada preserva a armadilha do denominador e não interpola o tenant."""

import inspect

import pytest
import sqlglot
from sqlglot import exp

from logidash.metrics.compilador import compilar
from logidash.metrics.definicoes import carregar_definicao
from logidash.metrics.erros import ConsultaInvalida


def _compilada(agregar_por: str | None = None):
    return compilar(carregar_definicao("otif").sql, agregar_por=agregar_por)


def test_filtro_de_tenant_agrupa_o_where_existente() -> None:
    arvore = sqlglot.parse_one(_compilada().sql, read="duckdb")
    conjuncao = arvore.args["where"].this
    assert isinstance(conjuncao, exp.And)
    assert isinstance(conjuncao.this, exp.Paren)
    assert "data_prometida_original" in conjuncao.this.sql(dialect="duckdb")
    assert "tenant_id" not in conjuncao.this.sql(dialect="duckdb")
    assert isinstance(conjuncao.expression, exp.EQ)


def test_where_filtra_prazo_prometido_e_nao_a_entrega() -> None:
    arvore = sqlglot.parse_one(_compilada().sql, read="duckdb")
    where = arvore.args["where"].sql(dialect="duckdb")
    assert "data_prometida_original" in where
    assert "data_entrega" not in where
    assert "tenant_id" in where
    texto = " ".join(expressao.sql(dialect="duckdb") for expressao in arvore.expressions)
    assert "data_entrega" in texto
    assert "qtd_entregue" in texto
    assert "qtd_pedida" in texto
    assert "NULLIF" in texto.upper()


def test_identificadores_sao_citados_e_parametros_nomeados() -> None:
    sql = _compilada(agregar_por="carrier_id").sql
    assert '"fact_shipment"' in sql
    assert '"tenant_id"' in sql
    assert '"carrier_id"' in sql
    assert "$tenant_id" in sql
    assert "$inicio" in sql
    assert "$fim" in sql
    assert "GROUP BY" in sql.upper()
    assert "tenant-a" not in sql
    arvore = sqlglot.parse_one(sql, read="duckdb")
    for identificador in arvore.find_all(exp.Identifier):
        assert identificador.args.get("quoted") is True


def test_compilador_nao_recebe_o_valor_do_tenant() -> None:
    parametros = inspect.signature(compilar).parameters
    assert "tenant_id" not in parametros
    assert "agregar_por" in parametros


def test_dimensao_fisica_de_transportadora_e_rejeitada() -> None:
    with pytest.raises(ConsultaInvalida, match="carrier_id"):
        _compilada(agregar_por="transportadora")
