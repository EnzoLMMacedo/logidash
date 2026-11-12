"""Contrato do gerador: spec sem tenant e resultado genérico do OTIF."""

from fastapi.testclient import TestClient

from logidash.api.aplicacao import criar_aplicacao
from logidash.api.gerador import spec_painel_otif

SPEC = spec_painel_otif().model_dump()


def _cliente() -> TestClient:
    return TestClient(criar_aplicacao())


def _resultado(token: str, spec: dict | None = None):
    return _cliente().post(
        "/api/paineis/resultado",
        headers={"Authorization": f"Bearer {token}"},
        json=SPEC if spec is None else spec,
    )


def _card(corpo: dict) -> dict:
    return next(widget for widget in corpo["widgets"] if widget["tipo"] == "kpi_card")


def _serie(widget: dict, nome: str) -> dict:
    return next(serie for serie in widget["series"] if serie["nome"] == nome)


def test_spec_nao_declara_tenant() -> None:
    resposta = _cliente().get("/api/paineis/spec")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert "tenant_id" not in corpo
    assert corpo["fonte"]["modo"] == "MATERIALIZE"
    assert corpo["filtros"][0]["campo"] == "data_prometida_original"
    assert [item["kpi"] for item in corpo["layout"]] == ["otif", "otif"]
    assert {item["tipo"] for item in corpo["layout"]} == {"kpi_card", "barra_horizontal"}


def test_resultado_otif_e_quarentena() -> None:
    resposta = _resultado("token-a")
    assert resposta.status_code == 200
    corpo = resposta.json()
    card = _card(corpo)
    assert card["rotulo"] == "OTIF"
    assert card["unidade"] == "fracao"
    assert card["formatacao"] == "fracao"
    assert card["meta"] == "0.95"
    assert _serie(card, "valor")["valor"] == "0.5"
    assert _serie(card, "numerador")["valor"] == "1"
    assert _serie(card, "denominador")["valor"] == "2"
    ids = {item["shipment_id"] for item in corpo["rejeicoes"]}
    assert "E-peso" in ids
    assert "E-b" not in ids
    assert "E-incompleta" not in ids


def test_outro_token_nao_ve_o_mesmo_resultado() -> None:
    corpo = _resultado("token-b").json()
    card = _card(corpo)
    assert _serie(card, "valor")["valor"] == "1"
    assert _serie(card, "denominador")["valor"] == "1"
    assert corpo["rejeicoes"] == []


def test_spec_com_tenant_e_rejeitado() -> None:
    spec = spec_painel_otif().model_dump()
    spec["tenant_id"] = "tenant-b"
    resposta = _resultado("token-a", spec)
    assert resposta.status_code == 422
    assert "token" in resposta.json()["detail"]


def test_kpi_fora_do_recorte_nao_entra() -> None:
    spec = spec_painel_otif().model_dump()
    spec["layout"] = [{"tipo": "kpi_card", "kpi": "giro_estoque", "largura": 3}]
    assert _resultado("token-a", spec).status_code == 404
    spec["layout"] = [{"tipo": "kpi_card", "kpi": "ocupacao_veiculo", "largura": 3}]
    assert _resultado("token-a", spec).status_code == 404


def test_json_invalido_nao_e_erro_interno() -> None:
    resposta = _cliente().post(
        "/api/paineis/resultado",
        headers={"Authorization": "Bearer token-a", "Content-Type": "application/json"},
        content="{",
    )
    assert resposta.status_code == 422


def test_openapi_expoe_o_resultado_generico() -> None:
    documento = _cliente().get("/openapi.json").json()
    assert "/api/paineis/spec" in documento["paths"]
    assert "/api/paineis/resultado" in documento["paths"]
    widget = documento["components"]["schemas"]["WidgetDashboard"]["properties"]
    assert {"rotulo", "unidade", "formatacao", "meta", "series"} <= set(widget)
