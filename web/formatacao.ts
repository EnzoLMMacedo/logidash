export function formatarFracao(valor: string | null): string {
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

export function formatarMedida(valor: string | null, formatacao: string): string {
  if (valor === null) {
    return "Sem embarques no período";
  }
  if (formatacao === "fracao") {
    return formatarFracao(valor);
  }
  return valor;
}

export function formatarData(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  if (!ano || !mes || !dia) {
    return iso;
  }
  return `${dia}/${mes}/${ano}`;
}

export function numeroDaSerie(valor: string | null): number | null {
  if (valor === null || valor.trim() === "") {
    return null;
  }
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : null;
}

export function somarContagens(valores: Array<string | null>): number {
  return valores.reduce((soma, valor) => soma + (numeroDaSerie(valor) ?? 0), 0);
}

export function rotuloVisivel(rotulo: string): string {
  const texto = rotulo.trim();
  return texto === "" ? "Sem rótulo" : texto;
}
