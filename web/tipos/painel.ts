export type SeriePainel = {
  nome: string;
  valor: number;
};

export type RejeicaoPainel = {
  indice_linha: number;
  shipment_id: string | null;
  regra: string;
  campo: string | null;
  mensagem: string;
};

export type PainelOtif = {
  rotulo: string;
  valor: string | null;
  unidade: string;
  numerador: number;
  denominador: number;
  agregacao: string;
  periodo_inicio: string;
  periodo_fim: string;
  series: SeriePainel[];
  rejeicoes: RejeicaoPainel[];
};
