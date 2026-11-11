"""OTIF por transportadora é razão de somas, nunca a média dos percentuais."""

from datetime import date
from decimal import Decimal

from tests.conftest import calcular, embarque


def test_razao_de_somas_nao_e_media_dos_otif(motor) -> None:
    linhas = [
        embarque("A1", carrier_id="A"),
        embarque("A2", carrier_id="A", qtd_entregue=9),
        embarque("A-fora", carrier_id="A", data_prometida_original=date(2026, 2, 2)),
    ]
    for indice in range(998):
        if indice < 988:
            linhas.append(embarque(f"B{indice}", carrier_id="B"))
        else:
            linhas.append(
                embarque(
                    f"B{indice}",
                    carrier_id="B",
                    data_entrega=None,
                    qtd_entregue=None,
                    status_final="EM_TRANSITO",
                )
            )

    resultado = calcular(motor, linhas, agregar_por="carrier_id")
    grupos = {grupo.chave: grupo for grupo in resultado.grupos}

    assert grupos["A"].numerador == 1
    assert grupos["A"].denominador == 2
    assert grupos["B"].numerador == 988
    assert grupos["B"].denominador == 998
    assert resultado.numerador == 989
    assert resultado.denominador == 1000
    assert resultado.valor == Decimal(989) / Decimal(1000)
    assert resultado.agregacao == "razao_de_somas"

    media = (grupos["A"].valor + grupos["B"].valor) / 2
    assert resultado.valor != media
    assert sum(grupo.numerador for grupo in resultado.grupos) == resultado.numerador
    assert sum(grupo.denominador for grupo in resultado.grupos) == resultado.denominador


def test_transportadora_nula_nao_sai_do_denominador(motor) -> None:
    linhas = [
        embarque("E1", carrier_id="A"),
        embarque(
            "E2",
            carrier_id=None,
            data_entrega=None,
            qtd_entregue=None,
            status_final="EM_TRANSITO",
        ),
    ]
    resultado = calcular(motor, linhas, agregar_por="carrier_id")
    assert resultado.numerador == 1
    assert resultado.denominador == 2
    assert resultado.valor == Decimal(1) / Decimal(2)
    assert [grupo.chave for grupo in resultado.grupos] == ["A", None]
