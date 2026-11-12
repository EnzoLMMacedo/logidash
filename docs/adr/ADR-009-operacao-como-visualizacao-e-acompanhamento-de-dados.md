---
id: ADR-009
titulo: Operação como visualização e acompanhamento de dados
status: Aceito
data: 2026-11-11
decisores: [Enzo]
tags: [logidash, adr, escopo, operacao, dados, cargas, emissoes]
relacionados:
  - "[[ADR-008-escopo-paineis-e-gestao-operacional]]"
  - "[[operacao]]"
  - "[[README]]"
  - "[[kpis]]"
  - "[[checklist]]"
  - "[[pendencias]]"
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
---

# ADR-009 — Operação como visualização e acompanhamento de dados

## Status

**Aceito** em 2026-11-11, por decisão de Enzo no time de desenvolvimento.

Refina o [[ADR-008-escopo-paineis-e-gestao-operacional]], que permanece aceito e **não foi editado**. O ADR-008 estabelece que o produto não se limita aos painéis de KPI; este ADR define o que essa operação é — e o que ela não é.

## Contexto

Depois do ADR-008, o time ainda não tinha a descrição da operação. Enzo esclareceu que, em vez de um processo operacional geral, o recorte é visualizar e acompanhar dados tabelados ou de banco de dados comuns de uma transportadora, referentes a cargas, emissões e outros conjuntos ainda a listar.

## Decisão

1. A “gestão operacional” do LogiDash, neste recorte, é **visualizar e acompanhar** dados já existentes em planilhas ou em bancos comuns de transportadora — não executar um processo operacional geral (criar viagem, alocar veículo, despachar ou baixar entrega), enquanto isso não for descrito nesta pasta por decisão posterior.
2. Os conjuntos de dados já nomeados por Enzo são **cargas** e **emissões**. A lista não está fechada: o “etc.” permanece em aberto e só entra no produto quando for escrito em [[operacao]].
3. O significado de “emissões” ainda não foi desambiguado nesta pasta (por exemplo, documentos fiscais versus emissões ambientais). Até essa decisão, o código não escolhe o significado.
4. A ingestão desses dados segue o [[ADR-001-ingestao-e-normalizacao]] (Excel/CSV ou SQL). A exibição segue o [[ADR-002-stack-renderizacao]] (Next.js, TypeScript, ECharts e `DashboardSpec`). Não se introduz um segundo frontend.
5. Campos, regras, estados e telas específicas de cargas e emissões só existem quando estiverem em [[operacao]] (e, se forem indicadores, no [[kpis]], com incremento de versão).

## Consequências

- O [[README]] e o [[operacao]] passam a usar este recorte, não o de um gerenciador de processo geral.
- Módulo de execução operacional (viagem, alocação, despacho) continua fora do código até haver descrição e decisão novas nesta pasta.
- Alterar esta decisão exige um ADR novo que substitua este.
