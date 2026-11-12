import * as echarts from "echarts";

export const NOME_TEMA_GRAFICOS = "logidash";

export type TemaGraficos = {
  fonte: string;
  destaque: string;
  neutro: string;
  texto: string;
};

function token(estilo: CSSStyleDeclaration, nome: string): string {
  return estilo.getPropertyValue(nome).trim();
}

export function prepararTemaGraficos(): TemaGraficos {
  const raiz = getComputedStyle(document.documentElement);
  const fonte = getComputedStyle(document.body).fontFamily;
  const destaque = token(raiz, "--cor-destaque");
  const neutro = token(raiz, "--cor-texto-discreto");
  const borda = token(raiz, "--cor-borda");
  const superficie = token(raiz, "--cor-superficie");
  const texto = token(raiz, "--cor-texto");
  const apoio = token(raiz, "--cor-texto-apoio");
  const eixo = {
    axisLine: { lineStyle: { color: borda } },
    axisTick: { lineStyle: { color: borda } },
    axisLabel: { color: apoio, fontFamily: fonte },
    splitLine: { lineStyle: { color: borda } },
  };

  echarts.registerTheme(NOME_TEMA_GRAFICOS, {
    color: [destaque, neutro],
    backgroundColor: "transparent",
    textStyle: { fontFamily: fonte, color: apoio },
    legend: { textStyle: { fontFamily: fonte, color: apoio } },
    tooltip: {
      backgroundColor: superficie,
      borderColor: borda,
      borderWidth: 1,
      textStyle: { fontFamily: fonte, color: texto },
      axisPointer: { lineStyle: { color: borda } },
    },
    categoryAxis: eixo,
    valueAxis: eixo,
    bar: {
      itemStyle: { color: destaque },
      label: { color: apoio, fontFamily: fonte },
    },
    pie: {
      itemStyle: { borderColor: superficie, borderWidth: 3 },
      label: { color: apoio, fontFamily: fonte },
    },
  });

  return { fonte, destaque, neutro, texto };
}

export function corDaFatia(nome: string, tema: TemaGraficos): string {
  if (nome === "no_prazo_completo") {
    return tema.destaque;
  }
  return tema.neutro;
}
