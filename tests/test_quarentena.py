"""Linha que viola o contrato não some e não entra no número."""

from datetime import date, datetime
from decimal import Decimal

from logidash.metrics.contrato_embarque import separar_embarques

from tests.conftest import calcular, embarque


def _regras(relatorio, shipment_id: str) -> set[str]:
    return {
        violacao.regra
        for violacao in relatorio.violacoes
        if violacao.shipment_id == shipment_id
    }


def test_regras_de_contrato_do_dicionario() -> None:
    linhas = [
        embarque("E-data", data_coleta=date(2026, 1, 20), data_entrega=date(2026, 1, 10)),
        embarque("E-peso", peso_bruto_kg=Decimal("0")),
        embarque("E-qtd", qtd_expedida=10, qtd_entregue=11),
        embarque("E-tentativa", tentativas_entrega=0),
        embarque("E-status", status_final="CANCELADO"),
        embarque("E-prazo", data_prometida_original=None),
        embarque("E-tipo", qtd_pedida=True),
        embarque("E-float", peso_bruto_kg=1.5),
        embarque("E-datahora", data_entrega=datetime(2026, 1, 9)),
        embarque("E-ok", peso_bruto_kg=None),
        "nao-e-registro",
    ]
    _validas, relatorio = separar_embarques(linhas, "tenant-a")
    assert _regras(relatorio, "E-data") == {"data_entrega_anterior_a_data_coleta"}
    assert _regras(relatorio, "E-peso") == {"peso_bruto_kg_nao_positivo"}
    assert _regras(relatorio, "E-qtd") == {"qtd_entregue_maior_que_qtd_expedida"}
    assert _regras(relatorio, "E-tentativa") == {"tentativas_entrega_menor_que_um"}
    assert _regras(relatorio, "E-status") == {"status_final_invalido"}
    assert _regras(relatorio, "E-prazo") == {"data_prometida_original_obrigatoria"}
    assert _regras(relatorio, "E-tipo") == {"tipo_invalido"}
    assert _regras(relatorio, "E-float") == {"tipo_invalido"}
    assert _regras(relatorio, "E-datahora") == {"tipo_invalido"}
    assert _regras(relatorio, "E-ok") == set()
    assert any(violacao.regra == "linha_invalida" for violacao in relatorio.violacoes)
    assert relatorio.quantidade_linhas == 10

    mensagens = {violacao.shipment_id: violacao.mensagem for violacao in relatorio.violacoes}
    assert mensagens["E-data"] == "data_entrega não pode ser anterior a data_coleta."
    assert mensagens["E-peso"] == "peso_bruto_kg deve ser maior que zero."
    assert mensagens["E-qtd"] == "qtd_entregue não pode ser maior que qtd_expedida."


def test_shipment_id_duplicado_nao_entra(motor) -> None:
    linhas = [
        embarque("E-ok"),
        embarque("E-dup", data_entrega=None, qtd_entregue=None, status_final="EM_TRANSITO"),
        embarque("E-dup", data_entrega=None, qtd_entregue=None, status_final="EM_TRANSITO"),
    ]
    _validas, relatorio = separar_embarques(linhas, "tenant-a")
    assert _regras(relatorio, "E-dup") == {"shipment_id_duplicado"}
    resultado = calcular(motor, linhas)
    assert resultado.numerador == 1
    assert resultado.denominador == 1
    assert resultado.valor == Decimal(1)
    assert _regras(resultado.rejeicoes, "E-dup") == {"shipment_id_duplicado"}
    assert _regras(resultado.rejeicoes, "E-ok") == set()


def test_rejeicao_acompanha_o_resultado_e_fica_fora_do_kpi(motor) -> None:
    linhas = [
        embarque("E-ok"),
        embarque(
            "E-peso",
            peso_bruto_kg=Decimal("0"),
            data_entrega=None,
            qtd_entregue=None,
            status_final="EM_TRANSITO",
        ),
        embarque("E-data", data_coleta=date(2026, 1, 20), data_entrega=date(2026, 1, 10)),
        embarque("E-qtd", qtd_expedida=10, qtd_entregue=11),
    ]
    resultado = calcular(motor, linhas)
    assert resultado.numerador == 1
    assert resultado.denominador == 1
    assert resultado.valor == Decimal(1)
    assert _regras(resultado.rejeicoes, "E-peso") == {"peso_bruto_kg_nao_positivo"}
    assert _regras(resultado.rejeicoes, "E-data") == {"data_entrega_anterior_a_data_coleta"}
    assert _regras(resultado.rejeicoes, "E-qtd") == {"qtd_entregue_maior_que_qtd_expedida"}
    assert _regras(resultado.rejeicoes, "E-ok") == set()
    assert {violacao.indice_linha for violacao in resultado.rejeicoes.violacoes} == {1, 2, 3}


def test_so_linhas_invalidas_nao_viram_zero(motor) -> None:
    resultado = calcular(motor, [embarque("E-peso", peso_bruto_kg=Decimal("-1"))])
    assert resultado.valor is None
    assert resultado.denominador == 0
    assert resultado.rejeicoes.quantidade_linhas == 1
    assert resultado.rejeicoes.violacoes[0].shipment_id == "E-peso"


def test_mesma_linha_pode_ter_varias_violacoes() -> None:
    linha = embarque(
        "E-varias",
        data_coleta=date(2026, 1, 20),
        data_entrega=date(2026, 1, 10),
        peso_bruto_kg=Decimal("0"),
        qtd_expedida=10,
        qtd_entregue=11,
    )
    _validas, relatorio = separar_embarques([linha], "tenant-a")
    assert _regras(relatorio, "E-varias") == {
        "data_entrega_anterior_a_data_coleta",
        "peso_bruto_kg_nao_positivo",
        "qtd_entregue_maior_que_qtd_expedida",
    }
