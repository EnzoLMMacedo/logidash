import * as echarts from "echarts";

export const NOME_TEMA_GRAFICOS = "logidash";

export type TemaGraficos = {
  fonte: string;
  destaque: string;
  neutro: string;
  borda: string;
  superficie: string;
  texto: string;
  apoio: string;
};

function token(estilo: CSSStyleDeclaration, nome: string): string {
  return estilo.getPropertyValue(nome).trim();
}

export function prepararTemaGraficos(): TemaGraficos {
  const raiz = getComputedStyle(document.documentElement);
  const tema: TemaGraficos = {
    fonte: getComputedStyle(document.body).fontFamily,
    destaque: token(raiz, "--cor-destaque"),
    neutro: token(raiz, "--cor-texto-discreto"),
    borda: token(raiz, "--cor-borda"),
    superficie: token(raiz, "--cor-superficie"),
    texto: token(raiz, "--cor-texto"),
    apoio: token(raiz, "--cor-texto-apoio"),
  };
  const eixo = {
    axisLine: { lineStyle: { color: tema.borda } },
    axisTick: { lineStyle: { color: tema.borda } },
    axisLabel: { color: tema.apoio, fontFamily: tema.fonte },
    splitLine: { lineStyle: { color: tema.borda } },
  };

  echarts.registerTheme(NOME_TEMA_GRAFICOS, {
    color: [tema.destaque, tema.neutro],
    backgroundColor: "transparent",
    textStyle: { fontFamily: tema.fonte, color: tema.apoio },
    legend: { textStyle: { fontFamily: tema.fonte, color: tema.apoio } },
    tooltip: {
      backgroundColor: tema.superficie,
      borderColor: tema.borda,
      borderWidth: 1,
      textStyle: { fontFamily: tema.fonte, color: tema.texto },
      axisPointer: { lineStyle: { color: tema.borda } },
    },
    categoryAxis: eixo,
    valueAxis: eixo,
    bar: {
      itemStyle: { color: tema.destaque },
      label: { color: tema.apoio, fontFamily: tema.fonte },
    },
    pie: {
      itemStyle: { borderColor: tema.superficie, borderWidth: 3 },
      label: { color: tema.apoio, fontFamily: tema.fonte },
    },
  });

  return tema;
}

export function corDaFatia(nome: string, tema: TemaGraficos): string {
  if (nome === "no_prazo_completo") {
    return tema.destaque;
  }
  return tema.neutro;
}
