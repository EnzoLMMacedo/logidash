---
id: pendencias
titulo: Pendências da documentação LogiDash
status: Aberto
data: 2026-11-11
tags: [logidash, pendencias, documentacao]
relacionados:
  - "[[README]]"
  - "[[kpis]]"
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
  - "[[ADR-003-medallion-com-quarentena]]"
  - "[[ADR-004-painel-como-especificacao-declarativa]]"
  - "[[ADR-005-docs-as-code-e-sincronia-obsidian]]"
  - "[[ADR-006-leitura-de-excel-massivo]]"
  - "[[ADR-007-otif-promessa-original]]"
---

# Pendências da documentação LogiDash

Registro das inconsistências e buracos já identificados na fonte da verdade. Nada aqui resolve a regra de negócio — só documenta o que ainda precisa de decisão do time.

Enquanto o [[ADR-005-docs-as-code-e-sincronia-obsidian]] estiver planejado, esta pasta continua sendo a única fonte da verdade; não há fluxo de sincronia improvisado.

## Inconsistências no dicionário de KPIs

### Identificadores mistos em inglês e português

A convenção do projeto pede código e identificadores em português sem acento (`data_prometida_original`). O dicionário, porém, mistura inglês e português: por exemplo `shipment_id`, `tenant_id`, `carrier_id`, `fact_shipment`, `otif`, `otd`, `in_full`, `first_attempt_rate` e `fill_rate`, ao lado de campos como `data_prometida_original` e `valor_frete`. Falta uma decisão explícita sobre o vocabulário canônico.

### Classe de agregação de `custo_por_kg`

A seção 1.2 de [[kpis]] cita “custo por kg” como exemplo de `media_ponderada`. O índice e a definição oficial de `custo_por_kg` declaram `razao_de_somas`, e a fórmula é razão das somas. A divergência precisa ser corrigida na fonte (com incremento de versão), sem o código escolher uma classe por conta própria.

### Classe de agregação de `cobertura_dias`

No índice de [[kpis]], `cobertura_dias` está declarado como `media_ponderada`, mas a fórmula vigente é razão das somas (`SUM(qtd_disponivel) / SUM(demanda_media_diaria)`). Também precisa de decisão na fonte, com incremento de versão; esta nota não escolhe a classe.

## Buracos no modelo canônico

Campos e tabelas usados em fórmulas, mas ausentes da seção 1.1 de [[kpis]]:

- `ocupacao_veiculo` depende de `veiculo_id` e de `dim_vehicle` (`capacidade_peso_kg`, `capacidade_volume_m3`), que não estão nos campos canônicos.
- `giro_estoque` consulta `fact_inventory_movement` (movimentos de saída), que não está descrita na seção 1.1.

Esses dois KPIs ficam de fora da implementação até o dicionário fechar o contrato.

## ADRs planejados, ainda sem decisão

Os arquivos abaixo existem como placeholders de índice. Título e status vêm do [[README]]; o corpo ainda não registra decisão.

| ADR | Assunto | Status |
| --- | --- | --- |
| [[ADR-003-medallion-com-quarentena]] | Medallion com quarentena — detalhamento | Planejado |
| [[ADR-004-painel-como-especificacao-declarativa]] | Painel como especificação declarativa | Planejado |
| [[ADR-005-docs-as-code-e-sincronia-obsidian]] | Docs-as-Code e sincronia com Obsidian | Planejado |
| [[ADR-006-leitura-de-excel-massivo]] | Estratégia de leitura de Excel massivo | Aguarda benchmark |
| [[ADR-007-otif-promessa-original]] | OTIF medido contra a promessa original | Planejado |

O [[ADR-005-docs-as-code-e-sincronia-obsidian]], quando escrito, deve descrever `scripts/sync_obsidian.py`. Até lá, notas do LogiDash são gravadas só nesta pasta.

## Cópia no repositório já divergente

O [PR #1](https://github.com/EnzoLMMacedo/logidash/pull/1) adicionou uma cópia em `docs/` no repositório (`docs/README.md`, `docs/kpis.md`, `docs/adr/` com ADR-001 e ADR-002). Esse conteúdo corresponde ao estado do vault **antes** da reorganização de 2026-11-11.

Em relação a esta pasta, essa cópia:

- não inclui `pendencias.md` nem os placeholders dos ADRs 003 a 007;
- não traz as referências a pendências acrescentadas em `kpis.md`;
- no `docs/README.md`, ainda descreve `scripts/sync_obsidian.py` como se a sincronia já existisse, embora o ADR-005 continue planejado.

A fonte da verdade permanece esta pasta. Enquanto o [[ADR-005-docs-as-code-e-sincronia-obsidian]] não for escrito, não há fluxo de sincronia: as duas cópias precisam ser tratadas como um risco de divergência, não como duas fontes equivalentes.
