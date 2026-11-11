"""SqlGuard: parse em AST, allowlist e bloqueio de DDL/DML.

A SQL executável só chega aqui como texto já emitido pelo compilador ou como
definição estática. Este módulo não monta comando por interpolação.
"""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from logidash.metrics.erros import (
    SqlRejeitada,
    mensagem_construcao_nao_permitida,
    mensagem_funcao_nao_permitida,
)

_TABELA_PERMITIDA = "fact_shipment"
_PARAMETROS_DEFINICAO = frozenset({"inicio", "fim"})
_PARAMETROS_CONSULTA = frozenset({"inicio", "fim", "tenant_id"})

_TIPOS_PERMITIDOS = frozenset(
    {
        exp.Select,
        exp.Alias,
        exp.From,
        exp.Where,
        exp.Group,
        exp.Div,
        exp.Identifier,
        exp.Table,
        exp.TableAlias,
        exp.Between,
        exp.Cast,
        exp.Nullif,
        exp.Column,
        exp.Placeholder,
        exp.Sum,
        exp.DataType,
        exp.DataTypeParam,
        exp.Count,
        exp.Literal,
        exp.Case,
        exp.Star,
        exp.If,
        exp.And,
        exp.Not,
        exp.LTE,
        exp.GTE,
        exp.EQ,
        exp.Is,
        exp.Null,
    }
)

_DDL = (
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Analyze,
    exp.Comment,
)
_DML = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Copy,
)

_CLAUSULAS_DEFINICAO = (
    "group",
    "order",
    "limit",
    "offset",
    "having",
    "joins",
    "with_",
    "distinct",
    "qualify",
    "laterals",
    "pivots",
    "hint",
)
_CLAUSULAS_CONSULTA = (
    "order",
    "limit",
    "offset",
    "having",
    "joins",
    "with_",
    "distinct",
    "qualify",
    "laterals",
    "pivots",
    "hint",
)


def analisar_sql(sql: str, *, dialeto: str | None) -> exp.Expression:
    try:
        if dialeto is None:
            arvores = sqlglot.parse(sql)
        else:
            arvores = sqlglot.parse(sql, read=dialeto)
    except ParseError as exc:
        raise SqlRejeitada("SQL rejeitada: não foi possível interpretar o comando.") from exc
    if len(arvores) != 1 or arvores[0] is None:
        raise SqlRejeitada("SQL rejeitada: apenas um comando é permitido.")
    return arvores[0]


def verificar_definicao(arvore: exp.Expression) -> None:
    _verificar(arvore, clausulas=_CLAUSULAS_DEFINICAO, parametros=_PARAMETROS_DEFINICAO)
    if _identificadores_tenant(arvore):
        raise SqlRejeitada(
            "SQL rejeitada: a definição do KPI não pode filtrar tenant_id. "
            "O motor injeta esse filtro a partir do token."
        )


def verificar_consulta(arvore: exp.Expression) -> None:
    _verificar(arvore, clausulas=_CLAUSULAS_CONSULTA, parametros=_PARAMETROS_CONSULTA)
    _verificar_filtro_tenant(arvore)


def _verificar(
    arvore: exp.Expression,
    *,
    clausulas: tuple[str, ...],
    parametros: frozenset[str],
) -> None:
    _rejeitar_raiz(arvore)
    for no in arvore.walk():
        if type(no) in _TIPOS_PERMITIDOS:
            continue
        if isinstance(no, exp.Anonymous):
            raise SqlRejeitada(mensagem_funcao_nao_permitida(no.name))
        if isinstance(no, exp.Func):
            raise SqlRejeitada(mensagem_funcao_nao_permitida(no.sql_name() or type(no).__name__))
        raise SqlRejeitada(mensagem_construcao_nao_permitida(type(no).__name__))
    _verificar_tabelas(arvore)
    _proibir_clausulas(arvore, clausulas)
    nomes = _nomes_placeholders(arvore)
    if nomes != parametros:
        raise SqlRejeitada("SQL rejeitada: parâmetros fora da lista permitida.")


def _rejeitar_raiz(arvore: exp.Expression) -> None:
    if isinstance(arvore, _DDL) or isinstance(arvore, exp.Command):
        raise SqlRejeitada("SQL rejeitada: comando DDL não é permitido.")
    if isinstance(arvore, _DML):
        raise SqlRejeitada("SQL rejeitada: comando DML não é permitido.")
    if type(arvore) is not exp.Select:
        raise SqlRejeitada("SQL rejeitada: apenas consulta de leitura é permitida.")


def _verificar_tabelas(arvore: exp.Expression) -> None:
    tabelas = list(arvore.find_all(exp.Table))
    if not tabelas:
        raise SqlRejeitada("SQL rejeitada: a consulta precisa ler fact_shipment.")
    for tabela in tabelas:
        alvo = tabela.this
        if not isinstance(alvo, exp.Identifier) or alvo.name.lower() != _TABELA_PERMITIDA:
            raise SqlRejeitada("SQL rejeitada: tabela ou função de leitura fora da allowlist.")


def _proibir_clausulas(arvore: exp.Expression, clausulas: tuple[str, ...]) -> None:
    for nome in clausulas:
        if arvore.args.get(nome):
            raise SqlRejeitada("SQL rejeitada: construção não permitida.")


def _nomes_placeholders(arvore: exp.Expression) -> set[str]:
    return {(placeholder.name or "").lower() for placeholder in arvore.find_all(exp.Placeholder)}


def _identificadores_tenant(arvore: exp.Expression) -> list[exp.Identifier]:
    return [
        identificador
        for identificador in arvore.find_all(exp.Identifier)
        if identificador.name.lower() == "tenant_id"
    ]


def _verificar_filtro_tenant(arvore: exp.Expression) -> None:
    seguros = 0
    for igualdade in arvore.find_all(exp.EQ):
        lados = (igualdade.this, igualdade.expression)
        colunas = [
            lado
            for lado in lados
            if isinstance(lado, exp.Column) and lado.name.lower() == "tenant_id"
        ]
        placeholders = [
            lado
            for lado in lados
            if isinstance(lado, exp.Placeholder) and (lado.name or "").lower() == "tenant_id"
        ]
        literais = [lado for lado in lados if isinstance(lado, exp.Literal)]
        if colunas and literais:
            raise SqlRejeitada(
                "SQL rejeitada: tenant_id só pode ser comparado ao parâmetro do token."
            )
        if len(colunas) == 1 and len(placeholders) == 1:
            seguros += 1
            continue
        if colunas:
            raise SqlRejeitada(
                "SQL rejeitada: tenant_id só pode ser comparado ao parâmetro do token."
            )
    colunas_tenant = [
        coluna for coluna in arvore.find_all(exp.Column) if coluna.name.lower() == "tenant_id"
    ]
    if seguros != 1 or len(colunas_tenant) != 1:
        raise SqlRejeitada(
            "SQL rejeitada: a consulta precisa do filtro de tenant injetado pelo motor."
        )
