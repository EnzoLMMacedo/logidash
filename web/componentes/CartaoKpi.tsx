import { GraficoSerie } from "@/componentes/GraficoSerie";
import { formatarMedida, numeroDaSerie, rotuloVisivel, somarContagens } from "@/formatacao";
import type { WidgetDashboard } from "@/tipos/painel";

export function CartaoKpi({ widget }: { widget: WidgetDashboard }) {
  const serieValor = widget.series.find((serie) => serie.nome === "valor");
  const fatias = widget.series.filter((serie) => serie.nome !== "valor");
  const vazio = somarContagens(fatias.map((fatia) => fatia.valor)) === 0;
  const percentual = formatarMedida(serieValor?.valor ?? null, widget.formatacao);

  return (
    <article className="cartao cartao-principal">
      <p className="kicker">Indicador</p>
      <h2>{widget.rotulo}</h2>
      <p className="valor">{percentual}</p>
      {serieValor?.valor != null && widget.formatacao === "fracao" ? (
        <p className="apoio">Fração {serieValor.valor.replace(".", ",")}</p>
      ) : null}
      {widget.meta ? <p className="apoio">Meta {formatarMedida(widget.meta, widget.formatacao)}</p> : null}
      {vazio ? (
        <p className="vazio">Sem embarques no período para compor o gráfico.</p>
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
