import { GraficoSerie } from "@/componentes/GraficoSerie";
import type { PainelOtif } from "@/tipos/painel";

export const dynamic = "force-dynamic";

const API = process.env.API_INTERNA_URL ?? "http://127.0.0.1:8000";
const PERIODO = { inicio: "2026-01-01", fim: "2026-01-31" };

type Propriedades = {
  searchParams: Promise<{ token?: string }>;
};

export default async function Pagina({ searchParams }: Propriedades) {
  const parametros = await searchParams;
  const tokenInformado = parametros.token?.trim() ?? "";
  const token = tokenInformado === "" ? "token-a" : tokenInformado;
  const consulta = await consultarPainel(token);

  return (
    <main>
      <h1>Painel de entregas</h1>
      <p>
        Período de {formatarData(PERIODO.inicio)} a {formatarData(PERIODO.fim)}. O tenant vem
        do token, não de um campo da tela.
      </p>
      <form method="get">
        <label>
          Token
          <input id="token" name="token" defaultValue={token} autoComplete="off" />
        </label>
        <button type="submit">Atualizar</button>
      </form>
      {consulta.ok ? <Painel painel={consulta.painel} /> : <p className="erro">{consulta.mensagem}</p>}
    </main>
  );
}

function Painel({ painel }: { painel: PainelOtif }) {
  return (
    <>
      <section className="cartao" aria-labelledby="titulo-indicador">
        <h2 id="titulo-indicador">{painel.rotulo}</h2>
        <p className="valor">{formatarFracao(painel.valor)}</p>
        {painel.valor !== null ? <p className="meta">Fração {painel.valor.replace(".", ",")}</p> : null}
        {painel.denominador > 0 ? (
          <p className="contagem">
            {painel.numerador} de {painel.denominador} embarques no denominador
          </p>
        ) : null}
        {painel.series.length > 0 ? <GraficoSerie series={painel.series} /> : null}
      </section>
      <section className="rejeicoes" aria-labelledby="titulo-quarentena">
        <h2 id="titulo-quarentena">Quarentena</h2>
        <p>Linhas que não entram na métrica.</p>
        {painel.rejeicoes.length === 0 ? (
          <p>Nenhuma linha ficou de fora da métrica.</p>
        ) : (
          <table>
            <caption>Embarques rejeitados pelo contrato</caption>
            <thead>
              <tr>
                <th scope="col">Embarque</th>
                <th scope="col">Linha</th>
                <th scope="col">Motivo</th>
              </tr>
            </thead>
            <tbody>
              {painel.rejeicoes.map((item) => (
                <tr key={`${item.indice_linha}-${item.regra}`}>
                  <td>{item.shipment_id ?? "Sem identificador"}</td>
                  <td>{item.indice_linha}</td>
                  <td>{item.mensagem}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}

async function consultarPainel(
  token: string,
): Promise<{ ok: true; painel: PainelOtif } | { ok: false; mensagem: string }> {
  try {
    const resposta = await fetch(`${API}/api/painel/otif`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ kpi: "otif", parametros: PERIODO }),
      cache: "no-store",
    });
    if (!resposta.ok) {
      const corpo = (await resposta.json().catch(() => null)) as { detail?: string } | null;
      return { ok: false, mensagem: corpo?.detail ?? "Falha ao consultar o painel." };
    }
    return { ok: true, painel: (await resposta.json()) as PainelOtif };
  } catch {
    return {
      ok: false,
      mensagem: "Não foi possível consultar o painel. Verifique se a API está em execução.",
    };
  }
}

function formatarFracao(valor: string | null): string {
  if (valor === null) {
    return "Sem embarques no período";
  }
  const numero = Number(valor);
  if (!Number.isFinite(numero)) {
    return valor;
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(numero);
}

function formatarData(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}
