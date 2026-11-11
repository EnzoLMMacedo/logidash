"""Falhas visíveis ao chamador do motor."""


class ErroLogidash(Exception):
    """Base das falhas de uso ou de proteção do motor."""


class SpecRejeitado(ErroLogidash):
    """O spec tentou declarar o tenant."""


class TokenInvalido(ErroLogidash):
    """O token não resolve um tenant."""


class ConsultaInvalida(ErroLogidash):
    """A consulta não tem a forma que o motor aceita."""


class KpiDesconhecido(ErroLogidash):
    """Não há definição versionada para o KPI pedido."""


class SqlRejeitada(ErroLogidash):
    """A SQL não passou no SqlGuard."""


class ErroDeAgregacao(ErroLogidash):
    """A razão das somas não fechou com o resultado da consulta."""


def mensagem_funcao_nao_permitida(nome: str) -> str:
    return f"SQL rejeitada: a função {nome} não está na allowlist."


def mensagem_construcao_nao_permitida(nome: str) -> str:
    return f"SQL rejeitada: construção não permitida ({nome})."
