---
id: logidash-moc
titulo: LogiDash — Índice de Conhecimento
aliases:
  - LogiDash
tags: [logidash, moc, indice]
relacionados:
  - "[[kpis]]"
  - "[[pendencias]]"
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
---

# LogiDash — Índice de Conhecimento

Gerador de painéis logísticos multi-cliente, alimentado por planilhas Excel ou bancos SQL.

## Fonte da verdade

Esta pasta é a **única fonte da verdade** do projeto. Regras de negócio, decisões de arquitetura e definições de indicadores vivem aqui em Markdown; o código apenas as executa.

Regra de governança: **se uma regra de negócio existe no código mas não existe aqui, ela é um bug de documentação.**

O [[ADR-005-docs-as-code-e-sincronia-obsidian]] (Docs-as-Code e sincronia com Obsidian) está planejado e, quando for escrito, deve descrever `scripts/sync_obsidian.py`. Enquanto isso não acontecer, as notas do LogiDash são gravadas **somente nesta pasta** — sem vault paralelo, pasta espelho ou fluxo de sincronia improvisado.

## Estrutura desta pasta

| Nota | Papel |
| --- | --- |
| Esta nota (`README.md`) | Índice de navegação do LogiDash |
| [[kpis]] | Dicionário vigente dos indicadores (fórmulas, tipos e agregação) |
| [[pendencias]] | Inconsistências e buracos já identificados, ainda sem decisão |
| `adr/` | Uma nota por ADR, numerada; aceito não se edita, é substituído por outro |

## Decisões de arquitetura

| ADR | Assunto | Status |
| --- | --- | --- |
| [[ADR-001-ingestao-e-normalizacao]] | Estratégia de ingestão e normalização (Excel versus SQL) | Aceito |
| [[ADR-002-stack-renderizacao]] | Stack de renderização e motor de dashboards | Aceito |
| [[ADR-003-medallion-com-quarentena]] | Medallion com quarentena — detalhamento | Planejado |
| [[ADR-004-painel-como-especificacao-declarativa]] | Painel como especificação declarativa | Planejado |
| [[ADR-005-docs-as-code-e-sincronia-obsidian]] | Docs-as-Code e sincronia com Obsidian | Planejado |
| [[ADR-006-leitura-de-excel-massivo]] | Estratégia de leitura de Excel massivo | Aguarda benchmark |
| [[ADR-007-otif-promessa-original]] | OTIF medido contra a promessa original | Planejado |

As notas com status Planejado ou Aguarda benchmark são placeholders de índice: têm título e status, mas **ainda não registram decisão**. Não devem ser lidas como regra nova.

## Modelo de negócio

- [[kpis]] — dicionário de KPIs logísticos com fórmulas, tipos e regras de agregação

## Pendências em aberto

Inconsistências e buracos já notados — inclusive identificadores mistos em inglês e português, a divergência de classe de agregação de `custo_por_kg`, e campos canônicos faltando em `ocupacao_veiculo` e `giro_estoque` — estão em [[pendencias]]. Registrá-los não os resolve; o código não deve escolher a regra no lugar do dicionário.

## Mapa mental do sistema

```mermaid
flowchart LR
    A["Excel ou SQL"] -->|ADR-001| B["Bronze · Silver · Gold"]
    B -->|kpis.md| C["Motor de KPI"]
    C -->|ADR-002| D["Painel no navegador"]
```

## Convenções do projeto

- Idioma: código e identificadores em português sem acento (`data_prometida_original`), mensagens ao usuário em português.
- Nomenclatura: `snake_case` em Python, `camelCase` em TypeScript, `snake_case` para IDs de KPI.
- Toda decisão arquitetural relevante vira ADR numerado, e ADR aceito não é editado — é substituído por outro.

## Personas de orquestração

Os ADRs aceitos listam como decisores Arquiteto, Copiloto e Revisor. As regras dessas personas (e das demais) estão no vault, fora desta pasta, em `AI-Orchestration/Skill/`:

- [[🧠_Architect]]
- [[✈️_Copilot]]
- [[🔎_Reviewer]]
- [[🛠️_Assistant]]
- [[👶_Intern]]

Essas notas não são fonte da verdade de regra de negócio do LogiDash.
