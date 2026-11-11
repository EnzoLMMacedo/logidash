"""OTIF como no dicionário: prazo original, completude e fração exata."""

from datetime import date
from decimal import Decimal

from tests.conftest import calcular, embarque


def test_denominador_usa_data_prometida_e_nao_descarta_nao_entregue(motor) -> None:
    linhas = [
        embarque("E-ok"),
        embarque(
            "E-nunca",
            data_prometida_original=date(2026, 1, 15),
            data_entrega=None,
            qtd_entregue=None,
            status_final="EM_TRANSITO",
        ),
        embarque(
            "E-fora",
            data_prometida_original=date(2026, 2, 2),
            data_entrega=date(2026, 1, 20),
        ),
    ]
    resultado = calcular(motor, linhas)
    assert resultado.numerador == 1
    assert resultado.denominador == 2
    assert resultado.valor == Decimal(1) / Decimal(2)
    assert resultado.agregacao == "razao_de_somas"
    assert resultado.rejeicoes.violacoes == ()


def test_entrega_pontual_e_incompleta_nao_conta(motor) -> None:
    linhas = [
        embarque("E-ok"),
        embarque("E-incompleta", qtd_entregue=9),
        embarque("E-atrasada", data_entrega=date(2026, 1, 20)),
    ]
    resultado = calcular(motor, linhas)
    assert resultado.numerador == 1
    assert resultado.denominador == 3
    assert resultado.valor == Decimal(1) / Decimal(3)
    assert resultado.rejeicoes.violacoes == ()


def test_entrega_no_dia_prometido_conta(motor) -> None:
    resultado = calcular(
        motor,
        [embarque("E1", data_prometida_original=date(2026, 1, 10), data_entrega=date(2026, 1, 10))],
    )
    assert resultado.numerador == 1
    assert resultado.valor == Decimal(1)


def test_quantidade_acima_do_pedido_conta_se_couber_na_expedicao(motor) -> None:
    resultado = calcular(
        motor,
        [embarque("E1", qtd_pedida=10, qtd_expedida=12, qtd_entregue=12)],
    )
    assert resultado.numerador == 1
    assert resultado.denominador == 1
    assert resultado.rejeicoes.violacoes == ()


def test_quantidade_entregue_nula_fica_no_denominador(motor) -> None:
    resultado = calcular(motor, [embarque("E1", qtd_entregue=None)])
    assert resultado.numerador == 0
    assert resultado.denominador == 1
    assert resultado.valor == Decimal(0)
    assert resultado.rejeicoes.violacoes == ()


def test_limites_do_periodo_sao_inclusivos(motor) -> None:
    linhas = [
        embarque(
            "E-ini",
            data_coleta=date(2025, 12, 31),
            data_prometida_original=date(2026, 1, 1),
            data_entrega=date(2026, 1, 1),
        ),
        embarque(
            "E-fim",
            data_coleta=date(2026, 1, 2),
            data_prometida_original=date(2026, 1, 31),
            data_entrega=date(2026, 1, 31),
        ),
        embarque(
            "E-antes",
            data_coleta=date(2025, 12, 1),
            data_prometida_original=date(2025, 12, 31),
            data_entrega=date(2025, 12, 31),
        ),
        embarque(
            "E-depois",
            data_coleta=date(2026, 1, 2),
            data_prometida_original=date(2026, 2, 1),
            data_entrega=date(2026, 2, 1),
        ),
    ]
    resultado = calcular(motor, linhas)
    assert resultado.numerador == 2
    assert resultado.denominador == 2
    assert resultado.valor == Decimal(1)


def test_sem_embarque_no_periodo_otif_e_nulo_e_nao_zero(motor) -> None:
    resultado = calcular(motor, [])
    assert resultado.valor is None
    assert resultado.numerador == 0
    assert resultado.denominador == 0
    assert resultado.rejeicoes.violacoes == ()


def test_so_falhas_validas_dao_zero_e_nao_nulo(motor) -> None:
    resultado = calcular(
        motor,
        [embarque("E1", data_entrega=None, qtd_entregue=None, status_final="EM_TRANSITO")],
    )
    assert resultado.numerador == 0
    assert resultado.denominador == 1
    assert resultado.valor == Decimal(0)
