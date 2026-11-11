"""O tenant sai do token. Um spec que o declare é rejeitado."""

from collections.abc import Mapping
from typing import Protocol

from logidash.metrics.erros import ConsultaInvalida, SpecRejeitado, TokenInvalido

_PROFUNDIDADE_MAXIMA = 32


class ResolvedorDeToken(Protocol):
    def resolver(self, token: str) -> str:
        """Devolve o tenant_id associado ao token."""


class ResolvedorDeTokenEmMemoria:
    """Mapa token → tenant para este recorte, sem provedor de identidade."""

    def __init__(self, tokens: Mapping[str, str]) -> None:
        self._tokens = dict(tokens)

    def resolver(self, token: str) -> str:
        if type(token) is not str or token == "":
            raise TokenInvalido("Token inválido. Não foi possível resolver o tenant.")
        try:
            tenant_id = self._tokens[token]
        except KeyError as exc:
            raise TokenInvalido("Token inválido. Não foi possível resolver o tenant.") from exc
        if type(tenant_id) is not str or tenant_id == "":
            raise TokenInvalido("Token inválido. Não foi possível resolver o tenant.")
        return tenant_id


def validar_spec(spec: object) -> None:
    if not isinstance(spec, Mapping):
        raise ConsultaInvalida("A consulta precisa ser um registro.")
    if _contem_chave(spec, "tenant_id", 0):
        raise SpecRejeitado(
            "O tenant_id não pode ser declarado no spec. Ele é resolvido pelo token."
        )


def _contem_chave(valor: object, chave: str, profundidade: int) -> bool:
    if profundidade > _PROFUNDIDADE_MAXIMA:
        raise ConsultaInvalida("A consulta tem aninhamento demais.")
    if isinstance(valor, Mapping):
        for item_chave, item in valor.items():
            if item_chave == chave or _contem_chave(item, chave, profundidade + 1):
                return True
        return False
    if isinstance(valor, (list, tuple)):
        return any(_contem_chave(item, chave, profundidade + 1) for item in valor)
    return False
