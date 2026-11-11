"""Embarques em memória para o painel local. Não há arquivo nem banco."""

from datetime import date
from decimal import Decimal


def embarque(shipment_id: str, **alteracoes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "shipment_id": shipment_id,
        "tenant_id": "tenant-a",
        "carrier_id": "transp-1",
        "origem_id": "ORIG",
        "destino_id": "DEST",
        "data_coleta": date(2026, 1, 2),
        "data_prometida_original": date(2026, 1, 10),
        "data_prometida_vigente": date(2026, 1, 20),
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


EMBARQUES: tuple[dict[str, object], ...] = (
    embarque("E-ok"),
    embarque("E-incompleta", qtd_entregue=9),
    embarque(
        "E-peso",
        peso_bruto_kg=Decimal("0"),
        data_entrega=None,
        qtd_entregue=None,
        status_final="EM_TRANSITO",
    ),
    embarque("E-b", tenant_id="tenant-b", carrier_id="transp-2"),
)

TOKENS_DEMONSTRACAO = {
    "token-a": "tenant-a",
    "token-b": "tenant-b",
}
