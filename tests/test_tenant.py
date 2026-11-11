"""tenant_id só vem do token. Spec que o declare é rejeitado."""

import inspect
from decimal import Decimal

import pytest

from logidash.metrics.erros import ConsultaInvalida, KpiDesconhecido, SpecRejeitado, TokenInvalido
from logidash.metrics.motor_kpi import MotorKpi

from tests.conftest import calcular, consulta, embarque


def test_executar_nao_aceita_tenant_id() -> None:
    parametros = inspect.signature(MotorKpi.executar).parameters
    assert "tenant_id" not in parametros
    assert "token" in parametros


def test_spec_com_tenant_e_rejeitado_antes_do_token(motor) -> None:
    with pytest.raises(SpecRejeitado, match="token"):
        motor.executar(
            token="token-inexistente",
            consulta=consulta(tenant_id="tenant-b"),
            embarques=[embarque("E1")],
        )


def test_tenant_aninhado_no_spec_e_rejeitado(motor) -> None:
    pedido = consulta()
    pedido["parametros"] = {
        "inicio": pedido["parametros"]["inicio"],
        "fim": pedido["parametros"]["fim"],
        "tenant_id": "tenant-b",
    }
    with pytest.raises(SpecRejeitado):
        motor.executar(token="token-a", consulta=pedido, embarques=[embarque("E1")])


def test_campo_desconhecido_nao_vira_dashboard(motor) -> None:
    with pytest.raises(ConsultaInvalida):
        calcular(motor, [embarque("E1")], layout=[{"tipo": "kpi_card"}])


def test_token_invalido_nao_devolve_dado(motor) -> None:
    with pytest.raises(TokenInvalido):
        calcular(motor, [embarque("E1")], token="nao-existe")


def test_tenants_nao_se_enxergam(motor) -> None:
    linhas = [
        embarque("E-a", tenant_id="tenant-a"),
        embarque(
            "E-b",
            tenant_id="tenant-b",
            carrier_id="outra",
            data_entrega=None,
            qtd_entregue=None,
            status_final="EM_TRANSITO",
            peso_bruto_kg=Decimal("0"),
        ),
    ]
    resultado_a = calcular(motor, linhas, token="token-a")
    resultado_b = calcular(motor, linhas, token="token-b")

    assert resultado_a.numerador == 1
    assert resultado_a.denominador == 1
    assert resultado_a.rejeicoes.violacoes == ()

    assert resultado_b.numerador == 0
    assert resultado_b.denominador == 0
    assert resultado_b.valor is None
    assert {item.shipment_id for item in resultado_b.rejeicoes.violacoes} == {"E-b"}


def test_tenant_malicioso_nao_injeta_sql(motor) -> None:
    linhas = [
        embarque("E-mal", tenant_id="tenant' OR '1'='1"),
        embarque("E-outro", tenant_id="tenant-a"),
    ]
    resultado = calcular(motor, linhas, token="token-malicioso")
    assert resultado.numerador == 1
    assert resultado.denominador == 1
    assert resultado.rejeicoes.violacoes == ()


def test_mesmo_shipment_em_outro_tenant_nao_e_duplicata(motor) -> None:
    linhas = [
        embarque("E1", tenant_id="tenant-a"),
        embarque("E1", tenant_id="tenant-b", qtd_entregue=1),
    ]
    resultado = calcular(motor, linhas, token="token-a")
    assert resultado.denominador == 1
    assert resultado.numerador == 1
    assert resultado.rejeicoes.violacoes == ()


def test_dimensao_e_kpi_fora_do_recorte(motor) -> None:
    with pytest.raises(ConsultaInvalida, match="carrier_id"):
        calcular(motor, [embarque("E1")], agregar_por="transportadora")
    with pytest.raises(KpiDesconhecido):
        calcular(motor, [embarque("E1")], kpi="ocupacao_veiculo")
    with pytest.raises(KpiDesconhecido):
        calcular(motor, [embarque("E1")], kpi="giro_estoque")
