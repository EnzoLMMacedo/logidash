"""Fumaça da API que permanece depois da rota antiga do painel."""

from fastapi.testclient import TestClient

from logidash.api.aplicacao import criar_aplicacao


def test_saude() -> None:
    resposta = TestClient(criar_aplicacao()).get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"situacao": "no_ar"}
