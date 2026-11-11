"""Motor de KPI. A fração publicada é a razão das somas, não a média dos grupos."""

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from logidash.metrics.compilador import compilar
from logidash.metrics.contexto_tenant import ResolvedorDeToken, validar_spec
from logidash.metrics.contrato_embarque import DIMENSAO_TRANSPORTADORA, separar_embarques
from logidash.metrics.definicoes import carregar_definicao
from logidash.metrics.erros import (
    ConsultaInvalida,
    ErroDeAgregacao,
    TokenInvalido,
)
from logidash.metrics.executor_duckdb import executar_consulta
from logidash.metrics.modelos import GrupoKpi, ResultadoKpi

_CHAVES_CONSULTA = frozenset({"kpi", "parametros", "agregar_por"})
_CHAVES_PARAMETROS = frozenset({"inicio", "fim"})
_TOLERANCIA = Decimal("0.0005")


class MotorKpi:
    def __init__(self, resolvedor: ResolvedorDeToken) -> None:
        if not hasattr(resolvedor, "resolver"):
            raise ConsultaInvalida("O motor precisa de um resolvedor de token.")
        self._resolvedor = resolvedor

    def executar(
        self,
        token: str,
        consulta: Mapping[str, object],
        embarques: Sequence[object],
    ) -> ResultadoKpi:
        validar_spec(consulta)
        self._validar_chaves(consulta)
        kpi_id = self._kpi(consulta)
        inicio, fim = self._periodo(consulta)
        agregar_por = self._dimensao(consulta)
        tenant_id = self._tenant_do_token(token)
        definicao = carregar_definicao(kpi_id)
        validas, relatorio = separar_embarques(embarques, tenant_id)
        parametros = {"inicio": inicio, "fim": fim, "tenant_id": tenant_id}
        total = executar_consulta(
            compilar(definicao.sql, agregar_por=None).sql,
            parametros,
            validas,
        )
        numerador, denominador = self._totais(total)
        grupos: tuple[GrupoKpi, ...] = ()
        if agregar_por is not None:
            linhas = executar_consulta(
                compilar(definicao.sql, agregar_por=agregar_por).sql,
                parametros,
                validas,
            )
            grupos = self._grupos(linhas, agregar_por, numerador, denominador)
        return ResultadoKpi(
            kpi=definicao.id,
            valor=_valor_exato(numerador, denominador),
            numerador=numerador,
            denominador=denominador,
            agregacao=definicao.agregacao,
            grupos=grupos,
            rejeicoes=relatorio,
        )

    def _validar_chaves(self, consulta: Mapping[str, object]) -> None:
        if set(consulta) - _CHAVES_CONSULTA:
            raise ConsultaInvalida("A consulta tem um campo que o motor não aceita.")

    def _kpi(self, consulta: Mapping[str, object]) -> str:
        if "kpi" not in consulta:
            raise ConsultaInvalida("A consulta precisa informar o KPI.")
        kpi = consulta["kpi"]
        if type(kpi) is not str:
            raise ConsultaInvalida("O campo kpi deve ser texto.")
        return kpi

    def _periodo(self, consulta: Mapping[str, object]) -> tuple[date, date]:
        parametros = consulta.get("parametros")
        if not isinstance(parametros, Mapping) or set(parametros) != _CHAVES_PARAMETROS:
            raise ConsultaInvalida("A consulta precisa dos parâmetros inicio e fim.")
        return _data("inicio", parametros["inicio"]), _data("fim", parametros["fim"])

    def _dimensao(self, consulta: Mapping[str, object]) -> str | None:
        if "agregar_por" not in consulta or consulta["agregar_por"] is None:
            return None
        dimensao = consulta["agregar_por"]
        if dimensao != DIMENSAO_TRANSPORTADORA:
            raise ConsultaInvalida("A dimensão precisa ser o campo canônico carrier_id.")
        return dimensao

    def _tenant_do_token(self, token: str) -> str:
        if type(token) is not str or token == "":
            raise TokenInvalido("Token inválido. Não foi possível resolver o tenant.")
        tenant_id = self._resolvedor.resolver(token)
        if type(tenant_id) is not str or tenant_id == "":
            raise TokenInvalido("Token inválido. Não foi possível resolver o tenant.")
        return tenant_id

    def _totais(self, linhas: list[dict[str, object]]) -> tuple[int, int]:
        if len(linhas) != 1:
            raise ErroDeAgregacao("A consulta total de OTIF não retornou uma linha.")
        return _conferir_linha(linhas[0])

    def _grupos(
        self,
        linhas: list[dict[str, object]],
        dimensao: str,
        numerador_total: int,
        denominador_total: int,
    ) -> tuple[GrupoKpi, ...]:
        grupos: list[GrupoKpi] = []
        for linha in linhas:
            numerador, denominador = _conferir_linha(linha)
            chave = linha.get(dimensao)
            if chave is not None and type(chave) is not str:
                raise ErroDeAgregacao("Resultado agregado inválido.")
            grupos.append(
                GrupoKpi(
                    dimensao=dimensao,
                    chave=chave,
                    valor=_valor_exato(numerador, denominador),
                    numerador=numerador,
                    denominador=denominador,
                )
            )
        soma_numerador = sum(grupo.numerador for grupo in grupos)
        soma_denominador = sum(grupo.denominador for grupo in grupos)
        if soma_numerador != numerador_total or soma_denominador != denominador_total:
            raise ErroDeAgregacao(
                "A agregação razao_de_somas não fechou entre o total e os grupos."
            )
        grupos.sort(key=lambda grupo: (grupo.chave is None, grupo.chave or ""))
        return tuple(grupos)


def _data(nome: str, valor: object) -> date:
    if type(valor) is not date:
        raise ConsultaInvalida(f"O parâmetro {nome} deve ser uma data.")
    return valor


def _valor_exato(numerador: int, denominador: int) -> Decimal | None:
    if denominador == 0:
        return None
    return Decimal(numerador) / Decimal(denominador)


def _conferir_linha(linha: Mapping[str, object]) -> tuple[int, int]:
    try:
        bruto_otif = linha["otif"]
        numerador = _inteiro(linha["numerador"])
        denominador = _inteiro(linha["denominador"])
    except KeyError as exc:
        raise ErroDeAgregacao("Resultado agregado inválido.") from exc
    if denominador == 0:
        if numerador != 0 or bruto_otif is not None:
            raise ErroDeAgregacao("OTIF deveria ser nulo quando o denominador é zero.")
        return 0, 0
    if bruto_otif is None:
        raise ErroDeAgregacao("O valor de OTIF não confere com a razão das somas.")
    esperado = Decimal(numerador) / Decimal(denominador)
    obtido = Decimal(str(bruto_otif))
    if abs(obtido - esperado) > _TOLERANCIA:
        raise ErroDeAgregacao("O valor de OTIF não confere com a razão das somas.")
    return numerador, denominador


def _inteiro(valor: object) -> int:
    if valor is None:
        return 0
    if isinstance(valor, bool) or isinstance(valor, float):
        raise ErroDeAgregacao("Resultado agregado inválido.")
    if isinstance(valor, int):
        return int(valor)
    if isinstance(valor, Decimal) and valor == valor.to_integral_value():
        return int(valor)
    raise ErroDeAgregacao("Resultado agregado inválido.")
