"""Contrato de fact_shipment e relatório de rejeição.

As regras vêm do dicionário canônico e do ADR-001: nulidade dos campos,
data_entrega >= data_coleta, peso_bruto_kg > 0, qtd_entregue <= qtd_expedida
e tentativas_entrega com mínimo 1. Linha inválida não entra no KPI.
"""

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal

from logidash.metrics.modelos import RelatorioRejeicao, ViolacaoContrato

STATUS_FINAIS = frozenset({"ENTREGUE", "EM_TRANSITO", "DEVOLVIDO", "EXTRAVIADO"})
DIMENSAO_TRANSPORTADORA = "carrier_id"

_CAMPOS_TEXTO_OPCIONAIS = ("carrier_id", "origem_id", "destino_id")
_CAMPOS_DATA_OPCIONAIS = ("data_coleta", "data_prometida_vigente", "data_entrega")
_CAMPOS_DECIMAL_OPCIONAIS = ("peso_cubado_kg", "volume_m3", "distancia_km")


def separar_embarques(
    linhas: Iterable[object],
    tenant_id: str,
) -> tuple[tuple[dict[str, object], ...], RelatorioRejeicao]:
    violacoes: list[ViolacaoContrato] = []
    candidatas: list[tuple[int, Mapping[str, object]]] = []

    for indice, linha in enumerate(linhas):
        if not _eh_registro(linha):
            violacoes.append(
                _violacao(
                    indice,
                    None,
                    "linha_invalida",
                    None,
                    "A linha não é um registro de embarque.",
                )
            )
            continue
        tenant_linha = linha.get("tenant_id")
        if type(tenant_linha) is str and tenant_linha != tenant_id:
            continue
        candidatas.append((indice, linha))

    por_indice: dict[int, list[ViolacaoContrato]] = {}
    ids_vistos: dict[str, list[int]] = {}
    for indice, linha in candidatas:
        encontradas = _validar_linha(indice, linha)
        por_indice[indice] = encontradas
        shipment_id = linha.get("shipment_id")
        if type(shipment_id) is str:
            ids_vistos.setdefault(shipment_id, []).append(indice)

    for shipment_id, indices in ids_vistos.items():
        if len(indices) < 2:
            continue
        for indice in indices:
            por_indice[indice].append(
                _violacao(
                    indice,
                    shipment_id,
                    "shipment_id_duplicado",
                    "shipment_id",
                    "shipment_id duplicado.",
                )
            )

    validas: list[dict[str, object]] = []
    for indice, linha in candidatas:
        da_linha = por_indice[indice]
        if da_linha:
            violacoes.extend(da_linha)
            continue
        validas.append(dict(linha))

    violacoes.sort(key=lambda item: item.indice_linha)
    return tuple(validas), RelatorioRejeicao(violacoes=tuple(violacoes))


def _eh_registro(linha: object) -> bool:
    if not isinstance(linha, Mapping):
        return False
    return all(type(chave) is str for chave in linha)


def _validar_linha(indice: int, linha: Mapping[str, object]) -> list[ViolacaoContrato]:
    violacoes: list[ViolacaoContrato] = []
    shipment_id = _texto_obrigatorio(linha, "shipment_id", indice, violacoes)
    _texto_obrigatorio(linha, "tenant_id", indice, violacoes)
    _data_obrigatoria(linha, "data_prometida_original", indice, shipment_id, violacoes)
    _inteiro_obrigatorio(linha, "qtd_pedida", indice, shipment_id, violacoes)
    _inteiro_obrigatorio(linha, "qtd_expedida", indice, shipment_id, violacoes)
    tentativas = _inteiro_obrigatorio(
        linha, "tentativas_entrega", indice, shipment_id, violacoes
    )
    status = _texto_obrigatorio(linha, "status_final", indice, violacoes)

    for campo in _CAMPOS_TEXTO_OPCIONAIS:
        _texto_opcional(linha, campo, indice, shipment_id, violacoes)
    data_coleta = _data_opcional(linha, "data_coleta", indice, shipment_id, violacoes)
    _data_opcional(linha, "data_prometida_vigente", indice, shipment_id, violacoes)
    data_entrega = _data_opcional(linha, "data_entrega", indice, shipment_id, violacoes)
    qtd_entregue = _inteiro_opcional(linha, "qtd_entregue", indice, shipment_id, violacoes)
    peso_bruto = _decimal_opcional(linha, "peso_bruto_kg", indice, shipment_id, violacoes)
    for campo in _CAMPOS_DECIMAL_OPCIONAIS:
        _decimal_opcional(linha, campo, indice, shipment_id, violacoes)

    if type(tentativas) is int and tentativas < 1:
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                "tentativas_entrega_menor_que_um",
                "tentativas_entrega",
                "tentativas_entrega deve ser no mínimo 1.",
            )
        )
    if type(status) is str and status not in STATUS_FINAIS:
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                "status_final_invalido",
                "status_final",
                "status_final inválido. Use ENTREGUE, EM_TRANSITO, DEVOLVIDO ou EXTRAVIADO.",
            )
        )
    # data_entrega e data_coleta são anuláveis. A desigualdade só corre
    # quando as duas datas existem.
    if (
        type(data_entrega) is date
        and type(data_coleta) is date
        and data_entrega < data_coleta
    ):
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                "data_entrega_anterior_a_data_coleta",
                "data_entrega",
                "data_entrega não pode ser anterior a data_coleta.",
            )
        )
    if peso_bruto is not None and peso_bruto <= 0:
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                "peso_bruto_kg_nao_positivo",
                "peso_bruto_kg",
                "peso_bruto_kg deve ser maior que zero.",
            )
        )
    qtd_expedida = linha.get("qtd_expedida")
    if (
        type(qtd_entregue) is int
        and type(qtd_expedida) is int
        and qtd_entregue > qtd_expedida
    ):
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                "qtd_entregue_maior_que_qtd_expedida",
                "qtd_entregue",
                "qtd_entregue não pode ser maior que qtd_expedida.",
            )
        )
    return violacoes


def _texto_obrigatorio(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    violacoes: list[ViolacaoContrato],
) -> str | None:
    shipment_id = _shipment_id_atual(linha)
    valor = linha.get(campo)
    if valor is None:
        violacoes.append(
            _violacao(
                indice,
                shipment_id if campo != "shipment_id" else None,
                f"{campo}_obrigatorio",
                campo,
                f"O campo {campo} é obrigatório.",
            )
        )
        return None
    if type(valor) is not str:
        violacoes.append(_tipo_invalido(indice, shipment_id, campo))
        return None
    return valor


def _data_obrigatoria(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    shipment_id: str | None,
    violacoes: list[ViolacaoContrato],
) -> date | None:
    valor = linha.get(campo)
    if valor is None:
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                f"{campo}_obrigatoria",
                campo,
                f"O campo {campo} é obrigatório.",
            )
        )
        return None
    if type(valor) is not date:
        violacoes.append(_tipo_invalido(indice, shipment_id, campo))
        return None
    return valor


def _inteiro_obrigatorio(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    shipment_id: str | None,
    violacoes: list[ViolacaoContrato],
) -> int | None:
    valor = linha.get(campo)
    if valor is None:
        violacoes.append(
            _violacao(
                indice,
                shipment_id,
                f"{campo}_obrigatoria",
                campo,
                f"O campo {campo} é obrigatório.",
            )
        )
        return None
    if type(valor) is not int:
        violacoes.append(_tipo_invalido(indice, shipment_id, campo))
        return None
    return valor


def _texto_opcional(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    shipment_id: str | None,
    violacoes: list[ViolacaoContrato],
) -> None:
    valor = linha.get(campo)
    if valor is not None and type(valor) is not str:
        violacoes.append(_tipo_invalido(indice, shipment_id, campo))


def _data_opcional(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    shipment_id: str | None,
    violacoes: list[ViolacaoContrato],
) -> date | None:
    valor = linha.get(campo)
    if valor is None:
        return None
    if type(valor) is not date:
        violacoes.append(_tipo_invalido(indice, shipment_id, campo))
        return None
    return valor


def _inteiro_opcional(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    shipment_id: str | None,
    violacoes: list[ViolacaoContrato],
) -> int | None:
    valor = linha.get(campo)
    if valor is None:
        return None
    if type(valor) is not int:
        violacoes.append(_tipo_invalido(indice, shipment_id, campo))
        return None
    return valor


def _decimal_opcional(
    linha: Mapping[str, object],
    campo: str,
    indice: int,
    shipment_id: str | None,
    violacoes: list[ViolacaoContrato],
) -> Decimal | None:
    valor = linha.get(campo)
    if valor is None:
        return None
    if type(valor) is int:
        return Decimal(valor)
    if type(valor) is Decimal:
        return valor
    violacoes.append(_tipo_invalido(indice, shipment_id, campo))
    return None


def _shipment_id_atual(linha: Mapping[str, object]) -> str | None:
    valor = linha.get("shipment_id")
    if type(valor) is str:
        return valor
    return None


def _tipo_invalido(indice: int, shipment_id: str | None, campo: str) -> ViolacaoContrato:
    return _violacao(
        indice,
        shipment_id,
        "tipo_invalido",
        campo,
        f"O campo {campo} tem tipo inválido.",
    )


def _violacao(
    indice: int,
    shipment_id: str | None,
    regra: str,
    campo: str | None,
    mensagem: str,
) -> ViolacaoContrato:
    return ViolacaoContrato(
        indice_linha=indice,
        shipment_id=shipment_id,
        regra=regra,
        campo=campo,
        mensagem=mensagem,
    )
