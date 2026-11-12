import { GraficoSerie } from "@/componentes/GraficoSerie";
import { formatarMedida, numeroDaSerie, rotuloVisivel, somarContagens } from "@/formatacao";
import type { WidgetDashboard } from "@/tipos/painel";

type SituacaoMeta = "dentro" | "fora" | "neutro";

function situacaoDaMeta(valor: string | null | undefined, meta: string | null): SituacaoMeta {
  const numero = numeroDaSerie(valor ?? null);
  const alvo = numeroDaSerie(meta);
  if (numero === null || alvo === null) {
    return "neutro";
  }
  // O widget não traz direção. Premissa visual: maior é melhor (valor >= meta).
  return numero >= alvo ? "dentro" : "fora";
}

export function CartaoKpi({ widget }: { widget: WidgetDashboard }) {
  const serieValor = widget.series.find((serie) => serie.nome === "valor");
  const fatias = widget.series.filter((serie) => serie.nome !== "valor");
  const vazio = somarContagens(fatias.map((fatia) => fatia.valor)) === 0;
  const percentual = formatarMedida(serieValor?.valor ?? null, widget.formatacao);
  const situacao = situacaoDaMeta(serieValor?.valor, widget.meta);
  const textoSituacao =
    situacao === "dentro" ? "Dentro da meta" : situacao === "fora" ? "Abaixo da meta" : null;

  return (
    <article className="cartao">
      <h2 className="rotulo">{widget.rotulo}</h2>
      <p className={situacao === "neutro" ? "valor" : `valor valor-${situacao}`}>{percentual}</p>
      {textoSituacao ? <p className={`status-meta status-${situacao}`}>{textoSituacao}</p> : null}
      {widget.meta ? <p className="apoio">Meta {formatarMedida(widget.meta, widget.formatacao)}</p> : null}
      {vazio ? (
        <p className="vazio">Sem embarques no período.</p>
      ) : (
        <>
          <ul className="contagens">
            {fatias.map((fatia, indice) => (
              <li key={`${fatia.nome}-${indice}`}>
                <span>{rotuloVisivel(fatia.rotulo)}</span>
                <strong>{fatia.valor ?? "0"}</strong>
              </li>
            ))}
          </ul>
          <GraficoSerie
            fatias={fatias.map((fatia) => ({
              nome: fatia.nome,
              rotulo: rotuloVisivel(fatia.rotulo),
              valor: numeroDaSerie(fatia.valor) ?? 0,
            }))}
            percentual={percentual}
          />
        </>
      )}
    </article>
  );
}
