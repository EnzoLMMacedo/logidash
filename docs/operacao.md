---
id: operacao
titulo: Visualização e acompanhamento de dados da transportadora
status: Parcial
data: 2026-11-11
tags: [logidash, operacao, escopo, cargas, emissoes]
relacionados:
  - "[[ADR-008-escopo-paineis-e-gestao-operacional]]"
  - "[[ADR-009-operacao-como-visualizacao-e-acompanhamento-de-dados]]"
  - "[[README]]"
  - "[[kpis]]"
  - "[[checklist]]"
  - "[[pendencias]]"
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
---

# Visualização e acompanhamento de dados da transportadora

Fonte da verdade do recorte operacional do produto, conforme o [[ADR-009-operacao-como-visualizacao-e-acompanhamento-de-dados]] (que refina o [[ADR-008-escopo-paineis-e-gestao-operacional]]).

O LogiDash visualiza e acompanha dados tabelados ou de banco de dados comuns de uma transportadora. Não é, neste recorte, um gerenciador de processo operacional geral.

Nada além do que estiver escrito aqui (e no [[kpis]], quando for indicador) entra no código.

A ingestão segue o [[ADR-001-ingestao-e-normalizacao]]; a interface segue o [[ADR-002-stack-renderizacao]] (Next.js, TypeScript e ECharts; sem Vue.js). O gerador de painéis (`DashboardSpec`) permanece o contrato de exibição já aceito.

## Conjuntos de dados

Recorte fechado por Enzo em 2026-11-11: **por enquanto só cargas e emissões**. Outro conjunto só entra quando for nomeado aqui.

- **Cargas** — ainda sem campos, estados, regras ou telas descritos.
- **Emissões** — documentos fiscais, como CT-e, MDF-e e afins. Os tipos nomeados são CT-e e MDF-e; “afins” são outros documentos fiscais ainda não listados e não devem ser inventados no código. Campos, estados, regras e telas ainda não foram descritos.

## Fora deste recorte

Enquanto não houver decisão e descrição novas nesta pasta, ficam de fora a execução de processo operacional geral — por exemplo criar viagem, alocar veículo, despachar ou baixar entrega.

## Entidades, estados e regras

Ainda não descritos para cargas nem para emissões. O modelo analítico do [[kpis]] não deve ser reutilizado de forma implícita como se já fosse o contrato desses conjuntos.

## Telas

Ainda não descritas. Telas de acompanhamento de cargas ou emissões, quando forem escritas, usam a stack do ADR-002. Esta nota não inventa layout nem fluxo.

## Relação com o dicionário de KPIs

Os indicadores do [[kpis]] continuam sendo a fonte da verdade analítica. Se o acompanhamento de cargas ou emissões exigir um indicador novo ou mudar fórmula ou campo, isso entra primeiro no dicionário, com incremento de versão.
