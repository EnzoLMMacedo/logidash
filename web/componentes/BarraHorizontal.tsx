"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { formatarMedida, numeroDaSerie, rotuloVisivel } from "@/formatacao";
import type { WidgetDashboard } from "@/tipos/painel";

export function BarraHorizontal({ widget }: { widget: WidgetDashboard }) {
  const caixa = useRef<HTMLDivElement>(null);
  const linhas = widget.series.map((serie) => ({
    nome: serie.nome,
    rotulo: rotuloVisivel(serie.rotulo),
    valor: serie.valor,
    numero: numeroDaSerie(serie.valor),
  }));
  const assinatura = linhas
    .map((linha) => `${linha.nome}\u0000${linha.rotulo}\u0000${linha.valor ?? ""}`)
    .join("\n");
  const resumo =
    linhas.length === 0
      ? "Nenhuma série neste período."
      : linhas
          .map((linha) => `${linha.rotulo}: ${linha.valor === null ? "Sem valor" : formatarMedida(linha.valor, widget.formatacao)}`)
          .join(". ");

  useEffect(() => {
    if (!caixa.current || linhas.length === 0) {
      return;
    }
    const textos = linhas.map((linha) =>
      linha.valor === null ? "Sem valor" : formatarMedida(linha.valor, widget.formatacao),
    );
    const maior = linhas.reduce((atual, linha) => Math.max(atual, linha.numero ?? 0), 0);
    const grafico = echarts.init(caixa.current);
    grafico.setOption({
      color: ["#0e4d5c"],
      aria: { enabled: true },
      grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: unknown) => {
          const lista = Array.isArray(params) ? params : [params];
          const item = lista[0] as { dataIndex?: number } | undefined;
          const indice = item?.dataIndex ?? 0;
          return `${linhas[indice]?.rotulo ?? ""}: ${textos[indice] ?? ""}`;
        },
      },
      xAxis: {
        type: "value",
        min: 0,
        max: widget.formatacao === "fracao" ? Math.max(1, maior) : undefined,
        axisLabel: {
          color: "#3d4d57",
          formatter: (valor: number) =>
            widget.formatacao === "fracao" ? formatarMedida(String(valor), widget.formatacao) : String(valor),
        },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: linhas.map((linha) => linha.rotulo),
        axisLabel: { color: "#14232c", width: 140, overflow: "truncate" },
      },
      series: [
        {
          type: "bar",
          data: linhas.map((linha) => linha.numero),
          barMaxWidth: 22,
          label: {
            show: true,
            position: "right",
            color: "#14232c",
            formatter: (params: { dataIndex?: number }) => textos[params.dataIndex ?? 0] ?? "",
          },
        },
      ],
    });
    const aoRedimensionar = () => grafico.resize();
    window.addEventListener("resize", aoRedimensionar);
    return () => {
      window.removeEventListener("resize", aoRedimensionar);
      grafico.dispose();
    };
  }, [assinatura, linhas, widget.formatacao]);

  return (
    <article className="cartao">
      <p className="kicker">Série</p>
      <h2>{widget.rotulo}</h2>
      {linhas.length === 0 ? (
        <p className="vazio">Nenhuma série neste período.</p>
      ) : (
        <div ref={caixa} className="grafico" role="img" aria-label={resumo} />
      )}
    </article>
  );
}
