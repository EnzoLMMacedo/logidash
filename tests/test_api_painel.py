"""Fumaça do contrato HTTP do painel. O cálculo continua no motor."""

from fastapi.testclient import TestClient

from logidash.api.aplicacao import criar_aplicacao

PERIODO = {"inicio": "2026-01-01", "fim": "2026-01-31"}


def _cliente() -> TestClient:
    return TestClient(criar_aplicacao())


def _painel(token: str, **extra: object):
    corpo: dict[str, object] = {"kpi": "otif", "parametros": dict(PERIODO)}
    corpo.update(extra)
    return _cliente().post(
        "/api/painel/otif",
        headers={"Authorization": f"Bearer {token}"},
        json=corpo,
    )


def test_saude() -> None:
    resposta = _cliente().get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "no_ar"}


def test_otif_e_quarentena_do_token_a() -> None:
    resposta = _painel("token-a")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["rotulo"] == "OTIF"
    assert corpo["unidade"] == "fracao"
    assert corpo["valor"] == "0.5"
    assert corpo["numerador"] == 1
    assert corpo["denominador"] == 2
    assert corpo["agregacao"] == "razao_de_somas"
    ids = {item["shipment_id"] for item in corpo["rejeicoes"]}
    assert "E-peso" in ids
    assert "E-b" not in ids
    assert "E-incompleta" not in ids
    assert any("peso_bruto_kg" in item["mensagem"] for item in corpo["rejeicoes"])


def test_outro_token_nao_ve_o_mesmo_numero() -> None:
    resposta = _painel("token-b")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["numerador"] == 1
    assert corpo["denominador"] == 1
    assert corpo["valor"] == "1"
    assert corpo["rejeicoes"] == []


def test_spec_com_tenant_e_rejeitado() -> None:
    resposta = _painel("token-a", tenant_id="tenant-b")
    assert resposta.status_code == 422
    assert "token" in resposta.json()["detail"]


def test_token_ausente_ou_invalido() -> None:
    sem_token = _cliente().post(
        "/api/painel/otif",
        json={"kpi": "otif", "parametros": PERIODO},
    )
    assert sem_token.status_code == 401
    invalido = _painel("nao-existe")
    assert invalido.status_code == 401


def test_openapi_expoe_o_painel() -> None:
    esquema = _cliente().get("/openapi.json")
    assert esquema.status_code == 200
    documento = esquema.json()
    operacao = documento["paths"]["/api/painel/otif"]["post"]
    assert operacao["responses"]["200"]
    nomes = documento["components"]["schemas"]["PainelResposta"]["properties"]
    assert {"valor", "numerador", "denominador", "rejeicoes", "rotulo"} <= set(nomes)
