"""DuckDB efêmero, uma instância por consulta, só com as linhas já filtradas.

O teto de memória é o da instância analítica. Não há arquivo nem banco externo.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

import duckdb
import pyarrow as pa

from logidash.metrics.erros import ConsultaInvalida, SqlRejeitada
from logidash.metrics.guardiao_sql import analisar_sql, verificar_consulta

_TETO_MEMORIA = "128MB"
_DECIMAL = pa.decimal128(18, 4)
_ESQUEMA = pa.schema(
    [
        ("shipment_id", pa.string()),
        ("tenant_id", pa.string()),
        ("carrier_id", pa.string()),
        ("origem_id", pa.string()),
        ("destino_id", pa.string()),
        ("data_coleta", pa.date32()),
        ("data_prometida_original", pa.date32()),
        ("data_prometida_vigente", pa.date32()),
        ("data_entrega", pa.date32()),
        ("qtd_pedida", pa.int64()),
        ("qtd_expedida", pa.int64()),
        ("qtd_entregue", pa.int64()),
        ("tentativas_entrega", pa.int64()),
        ("peso_bruto_kg", _DECIMAL),
        ("peso_cubado_kg", _DECIMAL),
        ("volume_m3", _DECIMAL),
        ("distancia_km", _DECIMAL),
        ("status_final", pa.string()),
    ]
)
_COLUNAS_DECIMAL = frozenset(
    {"peso_bruto_kg", "peso_cubado_kg", "volume_m3", "distancia_km"}
)
_COLUNAS_DATA = frozenset(
    {
        "data_coleta",
        "data_prometida_original",
        "data_prometida_vigente",
        "data_entrega",
    }
)


def executar_consulta(
    sql: str,
    parametros: Mapping[str, object],
    embarques: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    arvore = analisar_sql(sql, dialeto="duckdb")
    verificar_consulta(arvore)
    tabela = _tabela(embarques)
    conector = duckdb.connect(":memory:", config={"memory_limit": _TETO_MEMORIA})
    try:
        conector.register("fact_shipment", tabela)
        try:
            conector.execute(sql, dict(parametros))
        except duckdb.Error as exc:
            raise SqlRejeitada("SQL rejeitada: a consulta não pôde ser executada.") from exc
        descricao = conector.description
        if not descricao:
            raise SqlRejeitada("SQL rejeitada: a consulta não pôde ser executada.")
        nomes = [coluna[0].lower() for coluna in descricao]
        return [dict(zip(nomes, linha, strict=True)) for linha in conector.fetchall()]
    finally:
        conector.close()


def _tabela(embarques: Sequence[Mapping[str, object]]) -> pa.Table:
    registros = [_registro(linha) for linha in embarques]
    try:
        return pa.Table.from_pylist(registros, schema=_ESQUEMA)
    except (pa.ArrowInvalid, pa.ArrowTypeError, OverflowError) as exc:
        raise ConsultaInvalida("Não foi possível ler os embarques válidos.") from exc


def _registro(linha: Mapping[str, object]) -> dict[str, object]:
    registro: dict[str, object] = {}
    for campo in _ESQUEMA.names:
        valor = linha.get(campo)
        if campo in _COLUNAS_DECIMAL and type(valor) is int:
            valor = Decimal(valor)
        if campo in _COLUNAS_DATA and valor is not None and type(valor) is not date:
            raise ConsultaInvalida("Não foi possível ler os embarques válidos.")
        registro[campo] = valor
    return registro
