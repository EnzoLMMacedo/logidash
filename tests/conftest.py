"""Fixtures canônicas de fact_shipment. Nada aqui lê arquivo ou banco."""

from datetime import date
from decimal import Decimal

import pytest

from logidash.metrics.contexto_tenant import ResolvedorDeTokenEmMemoria
from logidash.metrics.motor_kpi import MotorKpi

INICIO = date(2026, 1, 1)
FIM = date(2026, 1, 31)


def embarque(shipment_id: str = "E1", **alteracoes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "shipment_id": shipment_id,
        "tenant_id": "tenant-a",
        "carrier_id": "transp-1",
        "origem_id": "ORIG",
        "destino_id": "DEST",
        "data_coleta": date(2026, 1, 2),
        "data_prometida_original": date(2026, 1, 10),
        "data_prometida_vigente": date(2026, 1, 12),
        "data_entrega": date(2026, 1, 9),
        "qtd_pedida": 10,
        "qtd_expedida": 10,
        "qtd_entregue": 10,
        "tentativas_entrega": 1,
        "peso_bruto_kg": Decimal("1.5000"),
        "peso_cubado_kg": Decimal("1.0000"),
        "volume_m3": Decimal("0.1000"),
        "distancia_km": Decimal("100.0000"),
        "status_final": "ENTREGUE",
    }
    base.update(alteracoes)
    return base


def consulta(**extra: object) -> dict[str, object]:
    dados: dict[str, object] = {
        "kpi": "otif",
        "parametros": {"inicio": INICIO, "fim": FIM},
    }
    dados.update(extra)
    return dados


def calcular(motor: MotorKpi, embarques: list[object], token: str = "token-a", **extra: object):
    return motor.executar(token=token, consulta=consulta(**extra), embarques=embarques)


@pytest.fixture
def motor() -> MotorKpi:
    return MotorKpi(
        ResolvedorDeTokenEmMemoria(
            {
                "token-a": "tenant-a",
                "token-b": "tenant-b",
                "token-malicioso": "tenant' OR '1'='1",
            }
        )
    )
