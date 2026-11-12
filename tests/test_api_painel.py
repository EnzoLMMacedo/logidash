"""Fumaça da API que permanece depois da rota antiga do painel."""

from fastapi.testclient import TestClient

from logidash.api.aplicacao import criar_aplicacao


def _cliente() -> TestClient:
    return TestClient(criar_aplicacao())


def test_saude() -> None:
    resposta = _cliente().get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "no_ar"}


def test_resultado_rejeita_token_ausente_ou_invalido() -> None:
    cliente = _cliente()
    spec = cliente.get("/api/paineis/spec")
    assert spec.status_code == 200
    corpo = spec.json()

    sem_token = cliente.post("/api/paineis/resultado", json=corpo)
    assert sem_token.status_code == 401

    invalido = cliente.post(
        "/api/paineis/resultado",
        headers={"Authorization": "Bearer nao-existe"},
        json=corpo,
    )
    assert invalido.status_code == 401
