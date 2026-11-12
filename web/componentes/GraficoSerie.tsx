"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { corDaFatia, NOME_TEMA_GRAFICOS, prepararTemaGraficos } from "@/componentes/temaGraficos";

export type FatiaGrafico = {
  nome: string;
  rotulo: string;
  valor: number;
};

type Propriedades = {
  fatias: FatiaGrafico[];
  percentual: string;
};

export function GraficoSerie({ fatias, percentual }: Propriedades) {
  const caixa = useRef<HTMLDivElement>(null);
  const dados = useRef({ fatias, percentual });
  dados.current = { fatias, percentual };
  const assinatura = `${percentual}\n${fatias.map((fatia) => `${fatia.nome}\u0000${fatia.rotulo}\u0000${fatia.valor}`).join("\n")}`;
  const resumo = `${percentual}. ${fatias.map((fatia) => `${fatia.rotulo}: ${fatia.valor}`).join(". ")}.`;

  useEffect(() => {
    const atuais = dados.current.fatias;
    const texto = dados.current.percentual;
    if (!caixa.current || atuais.length === 0) {
      return;
    }
    const tema = prepararTemaGraficos();
    const grafico = echarts.init(caixa.current, NOME_TEMA_GRAFICOS);
    grafico.setOption({
      aria: { enabled: true },
      tooltip: {
        trigger: "item",
        formatter: "{b}: {c}",
      },
      legend: {
        bottom: 0,
        icon: "circle",
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: tema.apoio, fontFamily: tema.fonte, fontSize: 13 },
      },
      graphic: {
        type: "text",
        left: "center",
        top: "36%",
        style: {
          text: texto,
          align: "center",
          fill: tema.texto,
          fontFamily: tema.fonte,
          fontSize: 28,
          fontWeight: 700,
        },
      },
      series: [
        {
          type: "pie",
          radius: ["58%", "78%"],
          center: ["50%", "44%"],
          avoidLabelOverlap: true,
          label: { show: false },
          itemStyle: { borderColor: tema.superficie, borderWidth: 3 },
          data: atuais.map((fatia) => ({
            name: fatia.rotulo,
            value: fatia.valor,
            itemStyle: { color: corDaFatia(fatia.nome, tema) },
          })),
        },
      ],
    });
    const aoRedimensionar = () => grafico.resize();
    window.addEventListener("resize", aoRedimensionar);
    return () => {
      window.removeEventListener("resize", aoRedimensionar);
      grafico.dispose();
    };
  }, [assinatura]);

  return <div ref={caixa} className="grafico" role="img" aria-label={resumo} />;
}
