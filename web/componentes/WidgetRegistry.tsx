import type { ComponentType } from "react";
import { BarraHorizontal } from "@/componentes/BarraHorizontal";
import { CartaoKpi } from "@/componentes/CartaoKpi";
import type { WidgetDashboard } from "@/tipos/painel";

export type PropriedadesWidget = {
  widget: WidgetDashboard;
};

export const WidgetRegistry: Record<string, ComponentType<PropriedadesWidget>> = {
  kpi_card: CartaoKpi,
  barra_horizontal: BarraHorizontal,
};
