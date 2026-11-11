"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { SeriePainel } from "@/tipos/painel";

type Propriedades = {
  series: SeriePainel[];
};

const CORES = ["#0e4d5c", "#c47b4a"];

export function GraficoSerie({ series }: Propriedades) {
  const caixa = useRef<HTMLDivElement>(null);
  const resumo = series.map((serie) => `${serie.nome}: ${serie.valor}`).join(". ");

  useEffect(() => {
    if (!caixa.current) {
      return;
    }
    const grafico = echarts.init(caixa.current);
    grafico.setOption({
      color: CORES,
      aria: { enabled: true },
      tooltip: { trigger: "item" },
      legend: {
        bottom: 0,
        icon: "circle",
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { color: "#14232c", fontSize: 13 },
      },
      series: [
        {
          type: "pie",
          radius: ["58%", "78%"],
          center: ["50%", "44%"],
          avoidLabelOverlap: true,
          label: { show: false },
          itemStyle: { borderColor: "#ffffff", borderWidth: 3 },
          data: series.map((serie) => ({ name: serie.nome, value: serie.valor })),
        },
      ],
    });
    const aoRedimensionar = () => grafico.resize();
    window.addEventListener("resize", aoRedimensionar);
    return () => {
      window.removeEventListener("resize", aoRedimensionar);
      grafico.dispose();
    };
  }, [series]);

  return <div ref={caixa} className="grafico" role="img" aria-label={resumo} />;
}
