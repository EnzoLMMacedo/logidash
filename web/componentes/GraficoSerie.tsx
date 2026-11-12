"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";

type Propriedades = {
  noPrazo: number;
  fora: number;
  percentual: string;
};

const CORES = ["#0e4d5c", "#c47b4a"];

export function GraficoSerie({ noPrazo, fora, percentual }: Propriedades) {
  const caixa = useRef<HTMLDivElement>(null);
  const resumo = `${percentual}. No prazo e completo: ${noPrazo}. Fora: ${fora}.`;

  useEffect(() => {
    if (!caixa.current || noPrazo + fora <= 0) {
      return;
    }
    const fatias = [
      { name: "No prazo e completo", value: noPrazo },
      { name: "Fora", value: fora },
    ];
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
          text: percentual,
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
          data: fatias,
        },
      ],
    });
    const aoRedimensionar = () => grafico.resize();
    window.addEventListener("resize", aoRedimensionar);
    return () => {
      window.removeEventListener("resize", aoRedimensionar);
      grafico.dispose();
    };
  }, [noPrazo, fora, percentual]);

  return <div ref={caixa} className="grafico" role="img" aria-label={resumo} />;
}
