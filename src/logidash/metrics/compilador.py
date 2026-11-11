"""Monta a consulta do KPI só com AST.

O CASE da fórmula é copiado da definição. O filtro de tenant entra como
parâmetro nomeado, nunca como literal. Identificadores saem citados pela
API do sqlglot.
"""

from dataclasses import dataclass

from sqlglot import exp

from logidash.metrics.contrato_embarque import DIMENSAO_TRANSPORTADORA
from logidash.metrics.erros import ConsultaInvalida, SqlRejeitada
from logidash.metrics.guardiao_sql import analisar_sql, verificar_consulta, verificar_definicao


@dataclass(frozen=True)
class ConsultaCompilada:
    sql: str


def compilar(sql_definicao: str, *, agregar_por: str | None) -> ConsultaCompilada:
    if agregar_por is not None and agregar_por != DIMENSAO_TRANSPORTADORA:
        raise ConsultaInvalida("A dimensão precisa ser o campo canônico carrier_id.")
    definicao = analisar_sql(sql_definicao, dialeto=None)
    verificar_definicao(definicao)
    if not isinstance(definicao, exp.Select):
        raise SqlRejeitada("SQL rejeitada: apenas consulta de leitura é permitida.")
    consulta = _montar(definicao, agregar_por)
    verificar_consulta(consulta)
    texto = consulta.sql(dialect="duckdb", identify=True)
    reanalise = analisar_sql(texto, dialeto="duckdb")
    verificar_consulta(reanalise)
    return ConsultaCompilada(sql=texto)


def _montar(definicao: exp.Select, agregar_por: str | None) -> exp.Select:
    consulta = definicao.copy()
    alias, nucleo, denominador = _extrair_razao(consulta)
    qualificador = _qualificador(consulta)
    expressoes: list[exp.Expression] = [
        alias.copy(),
        exp.alias_(nucleo.copy(), "numerador", quoted=True),
        exp.alias_(denominador.copy(), "denominador", quoted=True),
    ]
    if agregar_por is not None:
        coluna = exp.column(agregar_por, table=qualificador, quoted=True)
        expressoes.insert(0, exp.alias_(coluna.copy(), agregar_por, quoted=True))
        consulta.set("group", exp.Group(expressions=[coluna.copy()]))
    consulta.set("expressions", expressoes)
    _injetar_tenant(consulta, qualificador)
    for identificador in consulta.find_all(exp.Identifier):
        identificador.set("quoted", True)
    return consulta


def _extrair_razao(consulta: exp.Select) -> tuple[exp.Alias, exp.Expression, exp.Expression]:
    if len(consulta.expressions) != 1:
        raise SqlRejeitada("SQL rejeitada: a definição precisa de uma única expressão.")
    alias = consulta.expressions[0]
    if not isinstance(alias, exp.Alias):
        raise SqlRejeitada("SQL rejeitada: a definição precisa nomear o resultado.")
    divisao = alias.this
    if not isinstance(divisao, exp.Div):
        raise SqlRejeitada("SQL rejeitada: a fórmula precisa ser uma razão protegida por NULLIF.")
    nucleo: exp.Expression = divisao.this
    if isinstance(nucleo, exp.Cast):
        nucleo = nucleo.this
    protecao = divisao.expression
    if not isinstance(protecao, exp.Nullif):
        raise SqlRejeitada("SQL rejeitada: a divisão precisa estar protegida por NULLIF.")
    zero = protecao.expression
    if not isinstance(zero, exp.Literal) or zero.is_string or zero.this != "0":
        raise SqlRejeitada("SQL rejeitada: NULLIF precisa proteger divisão por zero.")
    return alias, nucleo, protecao.this


def _qualificador(consulta: exp.Select) -> str:
    origem = consulta.args.get("from_")
    if not isinstance(origem, exp.From) or not isinstance(origem.this, exp.Table):
        raise SqlRejeitada("SQL rejeitada: a consulta precisa ler fact_shipment.")
    tabela = origem.this
    alias = tabela.args.get("alias")
    if isinstance(alias, exp.TableAlias) and alias.name:
        return alias.name
    if type(alias) is str and alias != "":
        return alias
    if tabela.name:
        return tabela.name
    raise SqlRejeitada("SQL rejeitada: a consulta precisa ler fact_shipment.")


def _injetar_tenant(consulta: exp.Select, qualificador: str) -> None:
    predicado = exp.EQ(
        this=exp.column("tenant_id", table=qualificador, quoted=True),
        expression=exp.Placeholder(this="tenant_id"),
    )
    where = consulta.args.get("where")
    if not isinstance(where, exp.Where):
        consulta.set("where", exp.Where(this=predicado))
        return
    # O filtro existente fica entre parênteses para a precedência não
    # depender de OR continuar fora da allowlist.
    agrupado = exp.Paren(this=where.this.copy())
    where.set("this", exp.and_(agrupado, predicado, wrap=False))
