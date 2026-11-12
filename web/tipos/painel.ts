export type SerieDashboard = {
  nome: string;
  rotulo: string;
  valor: string | null;
  unidade: string;
};

export type WidgetDashboard = {
  tipo: string;
  rotulo: string;
  unidade: string;
  formatacao: string;
  meta: string | null;
  series: SerieDashboard[];
};

export type RejeicaoDashboard = {
  indice_linha: number;
  shipment_id: string | null;
  regra: string;
  campo: string | null;
  mensagem: string;
};

export type DashboardResult = {
  id: string;
  titulo: string;
  widgets: WidgetDashboard[];
  rejeicoes: RejeicaoDashboard[];
};

export type FiltroSpec = {
  campo: string;
  operador: string;
  valor: string[];
};

export type WidgetSpec = {
  tipo: string;
  kpi: string;
  largura: number;
  dimensao?: string | null;
  ordenar?: string | null;
  limite?: number | null;
};

export type DashboardSpec = {
  id: string;
  titulo: string;
  fonte: {
    source_id: string;
    modo: string;
  };
  filtros: FiltroSpec[];
  layout: WidgetSpec[];
};
