---
id: ADR-008
titulo: Escopo do produto — painéis e gestão operacional
status: Aceito
data: 2026-11-11
decisores: [Enzo]
tags: [logidash, adr, escopo, operacao, paineis]
relacionados:
  - "[[README]]"
  - "[[operacao]]"
  - "[[kpis]]"
  - "[[checklist]]"
  - "[[pendencias]]"
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
---

# ADR-008 — Escopo do produto — painéis e gestão operacional

## Status

**Aceito** em 2026-11-11, por decisão de Enzo no time de desenvolvimento.

Não substitui o [[ADR-001-ingestao-e-normalizacao]] nem o [[ADR-002-stack-renderizacao]]: a ingestão, o motor de KPI e o painel declarativo continuam válidos. Esta ADR amplia o escopo do produto.

## Contexto

Até esta decisão, a definição vigente no [[README]] era a de um gerador de painéis logísticos multi-cliente, alimentado por Excel ou SQL, com indicadores no [[kpis]].

Enzo registrou que o sistema precisa ser completo, será usado para vendas, e é um gerenciador completo do processo logístico de uma transportadora. Ficou decidido que o LogiDash **também** deve gerenciar a operação logística, além de medir e exibir indicadores.

## Decisão

1. O LogiDash não é só um gerador de painéis e KPIs. Ele também gerencia a operação logística de uma transportadora.
2. A descrição da operação — processos, entidades, estados, regras e telas — vive em [[operacao]]. Nada operacional entra no código enquanto não estiver escrito nessa nota (ou em notas ligadas a ela nesta pasta).
3. Esta ADR não inventa quais processos existem, nem o modelo de dados operacional, nem as telas. Isso ainda será escrito em [[operacao]].
4. Os recortes já documentados (motor de KPI, painel, ingestão Medallion, plataforma multi-cliente) seguem o [[checklist]] e os ADRs 001 e 002. Não são cancelados.

## Consequências

- O [[README]] passa a refletir este escopo.
- Qualquer módulo operacional ausente de [[operacao]] é, se implementado, um bug de documentação — e não deve ser implementado antes da descrição.
- Alterar esta decisão exige um ADR novo que substitua este.
