"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { NOME_TEMA_GRAFICOS, prepararTemaGraficos } from "@/componentes/temaGraficos";
import { formatarMedida, numeroDaSerie, rotuloVisivel } from "@/formatacao";
import type { WidgetDashboard } from "@/tipos/painel";

export function BarraHorizontal({ widget }: { widget: WidgetDashboard }) {
  const caixa = useRef<HTMLDivElement>(null);
  const linhas = widget.series.map((serie) => ({
    nome: serie.nome,
    rotulo: rotuloVisivel(serie.rotulo),
    valor: serie.valor,
    numero: numeroDaSerie(serie.valor),
    texto: serie.valor === null ? "Sem valor" : formatarMedida(serie.valor, widget.formatacao),
  }));
  const dados = useRef({ linhas, formatacao: widget.formatacao });
  dados.current = { linhas, formatacao: widget.formatacao };
  const assinatura = `${widget.formatacao}\n${linhas
    .map((linha) => `${linha.nome}\u0000${linha.rotulo}\u0000${linha.valor ?? ""}\u0000${linha.texto}`)
    .join("\n")}`;
  const resumo =
    linhas.length === 0
      ? "Sem séries no período."
      : linhas.map((linha) => `${linha.rotulo}: ${linha.texto}`).join(". ");

  useEffect(() => {
    const atuais = dados.current.linhas;
    const formatacao = dados.current.formatacao;
    if (!caixa.current || atuais.length === 0) {
      return;
    }
    const textos = atuais.map((linha) => linha.texto);
    const maior = atuais.reduce((atual, linha) => Math.max(atual, linha.numero ?? 0), 0);
    prepararTemaGraficos();
    const grafico = echarts.init(caixa.current, NOME_TEMA_GRAFICOS);
    grafico.setOption({
      aria: { enabled: true },
      grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: unknown) => {
          const lista = Array.isArray(params) ? params : [params];
          const item = lista[0] as { dataIndex?: number } | undefined;
          const indice = item?.dataIndex ?? 0;
          return `${atuais[indice]?.rotulo ?? ""}: ${textos[indice] ?? ""}`;
        },
      },
      xAxis: {
        type: "value",
        min: 0,
        max: formatacao === "fracao" ? Math.max(1, maior) : undefined,
        axisLabel: {
          formatter: (valor: number) =>
            formatacao === "fracao" ? formatarMedida(String(valor), formatacao) : String(valor),
        },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: atuais.map((linha) => linha.rotulo),
        axisLabel: { width: 140, overflow: "truncate" },
      },
      series: [
        {
          type: "bar",
          data: atuais.map((linha) => linha.numero),
          barMaxWidth: 22,
          label: {
            show: true,
            position: "right",
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
  }, [assinatura]);

  return (
    <article className="cartao">
      <h2 className="rotulo">{widget.rotulo}</h2>
      {linhas.length === 0 ? (
        <p className="vazio">Sem séries no período.</p>
      ) : (
        <div ref={caixa} className="grafico" role="img" aria-label={resumo} />
      )}
    </article>
  );
}
