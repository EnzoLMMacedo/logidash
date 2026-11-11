"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { SeriePainel } from "@/tipos/painel";

type Propriedades = {
  series: SeriePainel[];
};

export function GraficoSerie({ series }: Propriedades) {
  const caixa = useRef<HTMLDivElement>(null);
  const resumo = series.map((serie) => `${serie.nome}: ${serie.valor}`).join(". ");

  useEffect(() => {
    if (!caixa.current) {
      return;
    }
    const grafico = echarts.init(caixa.current);
    grafico.setOption({
      aria: { enabled: true },
      grid: { left: 24, right: 16, top: 16, bottom: 32, containLabel: true },
      xAxis: { type: "value", minInterval: 1 },
      yAxis: { type: "category", data: series.map((serie) => serie.nome) },
      series: [
        {
          type: "bar",
          data: series.map((serie) => serie.valor),
          itemStyle: { color: "#1d4e89" },
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
