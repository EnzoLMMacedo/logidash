import { WidgetRegistry } from "@/componentes/WidgetRegistry";
import { formatarData } from "@/formatacao";
import type { DashboardResult, DashboardSpec, RejeicaoDashboard } from "@/tipos/painel";

export const dynamic = "force-dynamic";

const API = process.env.API_INTERNA_URL ?? "http://127.0.0.1:8000";

type Propriedades = {
  searchParams: Promise<{ token?: string }>;
};

type Consulta =
  | { ok: true; spec: DashboardSpec; resultado: DashboardResult }
  | { ok: false; mensagem: string };

export default async function Pagina({ searchParams }: Propriedades) {
  const parametros = await searchParams;
  const tokenInformado = parametros.token?.trim() ?? "";
  const token = tokenInformado === "" ? "token-a" : tokenInformado;
  const consulta = await consultarPainel(token);
  const titulo = consulta.ok ? consulta.spec.titulo : "Painel de entregas";
  const intervalo = consulta.ok ? periodoDoSpec(consulta.spec) : null;

  return (
    <main>
      <header className="topo">
        <div>
          <p className="marca">LogiDash</p>
          <h1>{titulo}</h1>
        </div>
        {intervalo ? (
          <p className="periodo">
            {formatarData(intervalo.inicio)} a {formatarData(intervalo.fim)}
          </p>
        ) : null}
      </header>
      <section className="sessao" aria-label="Acesso">
        <div>
          <p className="kicker">Acesso</p>
          <p>O tenant vem do token, não de um campo da tela.</p>
        </div>
        <form method="get">
          <div>
            <label className="rotulo-campo" htmlFor="token">
              Token
            </label>
            <input id="token" name="token" defaultValue={token} autoComplete="off" />
          </div>
          <button type="submit">Atualizar</button>
        </form>
      </section>
      {consulta.ok ? (
        <Painel spec={consulta.spec} resultado={consulta.resultado} />
      ) : (
        <div className="erro" role="alert">
          <p className="erro-titulo">Falha ao consultar</p>
          <p className="apoio">{consulta.mensagem}</p>
        </div>
      )}
    </main>
  );
}

function Painel({ spec, resultado }: { spec: DashboardSpec; resultado: DashboardResult }) {
  return (
    <>
      {spec.layout.length === 0 ? (
        <p className="vazio">Nenhum indicador no período.</p>
      ) : (
        <section className="grade-widgets" aria-label="Indicadores">
          {spec.layout.map((item, indice) => {
            const widget = resultado.widgets[indice];
            const Componente = WidgetRegistry[item.tipo];
            if (!widget || widget.tipo !== item.tipo || !Componente) {
              return (
                <article className="cartao" key={`${item.tipo}-${indice}`}>
                  <h2 className="erro-titulo">Widget indisponível</h2>
                  <p className="apoio">Não foi possível exibir este cartão.</p>
                </article>
              );
            }
            return <Componente key={`${item.tipo}-${indice}`} widget={widget} />;
          })}
        </section>
      )}
      <Quarentena rejeicoes={resultado.rejeicoes} />
    </>
  );
}

function Quarentena({ rejeicoes }: { rejeicoes: RejeicaoDashboard[] }) {
  const linhas = rejeicoes.length;
  return (
    <section className="bloco-quarentena">
      <article className="cartao rejeicoes" aria-labelledby="titulo-quarentena">
        <div className="cabecalho-secao">
          <div>
            <p className="kicker">Fora da métrica</p>
            <h2 id="titulo-quarentena">Quarentena</h2>
          </div>
          <p className="selo">{textoLinhas(linhas)}</p>
        </div>
        <p className="apoio">Linhas que não entram na métrica.</p>
        {linhas === 0 ? (
          <p className="vazio">Nenhuma linha fora da métrica.</p>
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
              {rejeicoes.map((item) => (
                <tr key={`${item.indice_linha}-${item.regra}`}>
                  <td>{item.shipment_id ?? "Sem identificador"}</td>
                  <td>{item.indice_linha}</td>
                  <td>{item.mensagem}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}

async function consultarPainel(token: string): Promise<Consulta> {
  try {
    const specResposta = await fetch(`${API}/api/paineis/spec`, { cache: "no-store" });
    if (!specResposta.ok) {
      return { ok: false, mensagem: "Falha ao consultar o painel." };
    }
    const specBruto: unknown = await specResposta.json();
    if (!ehSpec(specBruto)) {
      return { ok: false, mensagem: "Falha ao consultar o painel." };
    }
    const resultadoResposta = await fetch(`${API}/api/paineis/resultado`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(specBruto),
      cache: "no-store",
    });
    if (!resultadoResposta.ok) {
      const corpo = (await resultadoResposta.json().catch(() => null)) as { detail?: string } | null;
      return { ok: false, mensagem: corpo?.detail ?? "Falha ao consultar o painel." };
    }
    const resultadoBruto: unknown = await resultadoResposta.json();
    if (!ehResultado(resultadoBruto)) {
      return { ok: false, mensagem: "Falha ao consultar o painel." };
    }
    return { ok: true, spec: specBruto, resultado: resultadoBruto };
  } catch {
    return {
      ok: false,
      mensagem: "Não foi possível consultar o painel. Verifique se a API está em execução.",
    };
  }
}

function periodoDoSpec(spec: DashboardSpec): { inicio: string; fim: string } | null {
  const filtro = spec.filtros.find(
    (item) => item.campo === "data_prometida_original" && item.operador === "entre" && item.valor.length === 2,
  );
  if (!filtro) {
    return null;
  }
  return { inicio: filtro.valor[0], fim: filtro.valor[1] };
}

function ehSpec(valor: unknown): valor is DashboardSpec {
  if (!valor || typeof valor !== "object") {
    return false;
  }
  const spec = valor as DashboardSpec;
  return typeof spec.titulo === "string" && Array.isArray(spec.layout) && Array.isArray(spec.filtros);
}

function ehResultado(valor: unknown): valor is DashboardResult {
  if (!valor || typeof valor !== "object") {
    return false;
  }
  const resultado = valor as DashboardResult;
  return Array.isArray(resultado.widgets) && Array.isArray(resultado.rejeicoes);
}

function textoLinhas(quantidade: number): string {
  return quantidade === 1 ? "1 linha" : `${quantidade} linhas`;
}
