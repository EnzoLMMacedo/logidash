"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";

export type FatiaGrafico = {
  nome: string;
  rotulo: string;
  valor: number;
};

type Propriedades = {
  fatias: FatiaGrafico[];
  percentual: string;
};

const CORES = ["#0e4d5c", "#c47b4a"];

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
    const grafico = echarts.init(caixa.current);
    grafico.setOption({
      color: CORES,
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
        textStyle: { color: "#14232c", fontSize: 13 },
      },
      graphic: {
        type: "text",
        left: "center",
        top: "36%",
        style: {
          text: texto,
          align: "center",
          fill: "#14232c",
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
          itemStyle: { borderColor: "#ffffff", borderWidth: 3 },
          data: atuais.map((fatia) => ({ name: fatia.rotulo, value: fatia.valor })),
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
