---
id: checklist
titulo: Checklist de etapas do LogiDash
status: Aberto
data: 2026-11-11
tags: [logidash, checklist, etapas, acompanhamento]
relacionados:
  - "[[README]]"
  - "[[kpis]]"
  - "[[pendencias]]"
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
  - "[[ADR-003-medallion-com-quarentena]]"
  - "[[ADR-004-painel-como-especificacao-declarativa]]"
  - "[[ADR-005-docs-as-code-e-sincronia-obsidian]]"
  - "[[ADR-006-leitura-de-excel-massivo]]"
  - "[[ADR-007-otif-promessa-original]]"
  - "[[ADR-008-escopo-paineis-e-gestao-operacional]]"
  - "[[ADR-009-operacao-como-visualizacao-e-acompanhamento-de-dados]]"
  - "[[operacao]]"
---

# Checklist de etapas do LogiDash

Acompanhamento das etapas, da arquitetura à entrega do escopo documentado. A fonte da verdade continua sendo esta pasta. Itens marcados como feitos correspondem ao que já entrou no repositório ou foi aceito em ADR; o restante vem dos ADRs, do [[kpis]] e das [[pendencias]] — sem inventar etapa, produto ou regra que não esteja nesses documentos.

Legenda: `[x]` feito · `[ ]` em aberto · bloqueios e decisões pendentes aparecem explícitos, não escondidos.

## 1. Arquitetura e governança

Decisões já aceitas (ADR aceito não se edita; é substituído por outro):

- [x] [[ADR-001-ingestao-e-normalizacao]] — porta única `SourceConnector`, Arrow, Medallion com quarentena, Bronze em Parquet, mapeamento semântico com humano no circuito
- [x] [[ADR-002-stack-renderizacao]] — FastAPI, Next.js e TypeScript, ECharts, react-grid-layout, DuckDB efêmero, painel como `DashboardSpec`, isolamento em três camadas, SqlGuard
- [x] Convenção de não trocar o frontend para Vue.js sem ADR novo que substitua o ADR-002 (pedido de 2026-11-11 recusado; a stack vigente permanece)
- [x] [[ADR-008-escopo-paineis-e-gestao-operacional]] — o produto não se limita aos painéis de KPI
- [x] [[ADR-009-operacao-como-visualizacao-e-acompanhamento-de-dados]] — operação como visualização e acompanhamento de dados (cargas, emissões), não um processo geral

ADRs previstos no índice, ainda sem decisão registrada (placeholders):

- [ ] [[ADR-003-medallion-com-quarentena]] — detalhamento do Medallion com quarentena
- [ ] [[ADR-004-painel-como-especificacao-declarativa]] — detalhamento do painel como especificação declarativa
- [ ] [[ADR-005-docs-as-code-e-sincronia-obsidian]] — Docs-as-Code e `scripts/sync_obsidian.py`
- [ ] [[ADR-006-leitura-de-excel-massivo]] — escolha do leitor de Excel, após o benchmark
- [ ] [[ADR-007-otif-promessa-original]] — formalizar o OTIF contra a promessa original (a regra vigente já está no [[kpis]])

Questões em aberto já documentadas nos ADRs aceitos:

- [ ] Benchmark de leitura de Excel (`python-calamine` versus leitor SAX em streaming, arquivo real de 200 MB) — trava o ADR-006
- [ ] Estratégia de ingestão incremental SQL (marca d'água, chave crescente ou captura de mudanças)
- [ ] Se o usuário final poderá editar o `DashboardSpec` pela interface
- [ ] Provedor de identidade (OIDC gerenciado versus autenticação própria)

## 2. Documentação (fonte da verdade)

- [x] Índice em [[README]]
- [x] Dicionário vigente [[kpis]] (versão 1.0.0, 20 indicadores)
- [x] ADRs 001 e 002 aceitos, sem edição posterior
- [x] [[pendencias]] criadas e inconsistências registradas
- [x] Placeholders dos ADRs 003 a 007
- [x] Cópia em `docs/` no repositório alinhada a esta pasta no [PR #1](https://github.com/EnzoLMMacedo/logidash/pull/1)
- [ ] Resolver no dicionário (com incremento de versão), antes do código escolher no lugar da fonte:
  - identificadores mistos em inglês e português
  - classe de agregação de `custo_por_kg`
  - classe de agregação de `cobertura_dias`
  - campos canônicos de `ocupacao_veiculo` (`veiculo_id`, `dim_vehicle`)
  - descrição de `fact_inventory_movement` para `giro_estoque`
- [ ] Escrever de fato os ADRs 003 a 007
- [ ] Implementar a sincronia docs-as-code somente quando o ADR-005 for aceito (sem fluxo improvisado até lá)

## 3. Motor de KPI (primeiro recorte)

Escopo combinado: motor testável com fixtures, sem planilha e sem banco.

- [x] Definição e cálculo de `otif` conforme o dicionário (denominador em `data_prometida_original`, incompleto não conta, `razao_de_somas`)
- [x] Quarentena visível: linha inválida não entra no número e aparece no relatório de rejeição
- [x] `tenant_id` só do token; spec que o declara é rejeitado
- [x] SqlGuard (parse em AST, sem interpolação de SQL)
- [x] Testes, inclusive o caso em que a entrega passa de `data_prometida_original` e cabe em `data_prometida_vigente`
- [x] [PR #1](https://github.com/EnzoLMMacedo/logidash/pull/1) mesclado em `main`

Ainda não faz parte deste recorte (e continua em aberto no produto):

- [ ] Demais KPIs do [[kpis]], além de `otif`
- [ ] `ocupacao_veiculo` e `giro_estoque` — bloqueados até o dicionário fechar o contrato canônico

## 4. Painel mínimo (segundo recorte)

Primeiro corte visual, ainda na stack do ADR-002 (Next.js, TypeScript, ECharts). Não é o gerador completo de painéis.

- [x] Página com OTIF e quarentena visível no [PR #2](https://github.com/EnzoLMMacedo/logidash/pull/2)
- [x] Acesso local documentado no PR: API em `:8000`, página em [http://localhost:3000](http://localhost:3000), tokens de demo `token-a` e `token-b`
- [x] Revisão e validação sem bloqueio no commit `c2307f2`
- [x] Revisão do commit visual `7786e37` sem bloqueio
- [ ] Merge do PR #2 em `main`, quando o time decidir
- [ ] Endereço público de acesso (ainda não existe; o acesso atual é local)

## 5. Ingestão e pipeline Medallion

Previsto no [[ADR-001-ingestao-e-normalizacao]]; ainda não entregue no código deste recorte.

- [ ] Porta `SourceConnector` com adaptadores Excel/CSV e SQL
- [ ] Fronteira em Apache Arrow (`RecordBatch` + `SourceSchema`)
- [ ] Bronze materializado em Parquet, com linhagem (hash e timestamp)
- [ ] Silver tipado, canônico e validado (Pandera, regras de domínio)
- [ ] Gold em *star schema*
- [ ] Quarentena explícita no fluxo de ingestão, visível no painel
- [ ] Perfilagem (amostra de no máximo 1.000 linhas)
- [ ] Mapeamento semântico em cascata (SourceSpec, dicionário em `docs/ontologia/`, sugestão com confirmação humana)
- [ ] Streaming com teto de memória; defesas de upload (zip bomb, teto de bytes, URL assinada)
- [ ] Credenciais de banco só por `credencial_ref` no cofre; usuário SQL somente-leitura
- [ ] Modo `FEDERATE` (exceção controlada) apenas quando necessário
- [ ] Ingestão incremental para fontes SQL (depende da questão em aberto do ADR-001)
- [ ] Benchmark e ADR-006, antes de fixar o leitor de Excel massivo

## 6. Dicionário de KPIs no motor

Nenhum KPI deve existir no código sem existir antes no [[kpis]]. Alteração de fórmula exige incremento de versão.

### Entrega e transporte

- [x] `otif`
- [ ] `otd`
- [ ] `in_full`
- [ ] `lead_time_medio`
- [ ] `desvio_prazo_dias`
- [ ] `first_attempt_rate`
- [ ] `taxa_ocorrencias`
- [ ] `taxa_reentrega`
- [ ] `taxa_devolucao`

### Custo de frete

- [ ] `frete_sobre_vendas`
- [ ] `custo_por_km`
- [ ] `custo_por_kg` — também bloqueado pela divergência de classe de agregação nas [[pendencias]]
- [ ] `custo_por_entrega`
- [ ] `aderencia_tabela`
- [ ] `ocupacao_veiculo` — bloqueado: faltam `veiculo_id` e `dim_vehicle` nos campos canônicos

### Estoque e armazém

- [ ] `giro_estoque` — bloqueado: falta `fact_inventory_movement` na seção 1.1
- [ ] `cobertura_dias` — também há divergência de classe de agregação nas [[pendencias]]
- [ ] `taxa_ruptura`
- [ ] `acuracidade_inventario`
- [ ] `fill_rate`

## 7. Gerador de painéis (produto completo)

Previsto no [[ADR-002-stack-renderizacao]] e a detalhar no [[ADR-004-painel-como-especificacao-declarativa]]. O corte do PR #2 é um passo, não o encerramento desta etapa.

- [ ] `DashboardSpec` como contrato declarativo (fonte, filtros, KPIs, layout)
- [ ] `SpecResolver`, `QueryPlanner` e `SqlGuard` no caminho de toda consulta do painel
- [ ] Frontend deliberadamente sem regra logística (`DashboardResult` genérico)
- [ ] `WidgetRegistry`, grade arrastável (react-grid-layout) e gráficos em ECharts
- [ ] KPI novo entra sem deploy de frontend (definição no servidor)
- [ ] `tenant_id` nunca vem do spec (já vale no motor; precisa continuar no painel completo)
- [ ] Marca branca
- [ ] Decidir e, se for o caso, implementar edição do spec pelo usuário final (questão em aberto do ADR-002)
- [ ] Cliente TypeScript gerado do OpenAPI

## 8. Plataforma multi-cliente

- [x] Isolamento de tenant no motor de KPI do primeiro recorte (token + DuckDB efêmero)
- [ ] PostgreSQL de metadados com Row-Level Security (`SET LOCAL app.tenant_id`)
- [ ] Prefixo por cliente no armazenamento e credenciais temporárias restritas
- [ ] Login e autorização granular (painel, fonte, filial)
- [ ] Escolha e implantação do provedor de identidade
- [ ] Cofre de credenciais para fontes SQL
- [ ] Cache de consulta endereçado por conteúdo (mitigação prevista no ADR-002)

## 9. Qualidade e critério de release

Já exigidos como porta de qualidade, não como “depois”:

- [x] Testes do motor sem arquivo e sem banco
- [x] CI de testes no PR #1 (e job `web` no PR #2)
- [x] SqlGuard e isolamento de tenant no recorte do motor
- [ ] Manter SqlGuard, quarentena visível e `tenant_id` só do token em todo recorte seguinte
- [ ] Testes de isolamento entre tenants no armazenamento e no banco de metadados, quando essas camadas existirem

## 10. Visualização e acompanhamento de dados

Decidido no [[ADR-009-operacao-como-visualizacao-e-acompanhamento-de-dados]], que refina o [[ADR-008-escopo-paineis-e-gestao-operacional]]. Não é um gerenciador de processo operacional geral.

- [x] Recorte registrado: visualizar e acompanhar dados tabelados ou de banco de uma transportadora
- [x] Conjuntos do recorte, por enquanto: só cargas e emissões
- [x] Emissões são documentos fiscais (CT-e, MDF-e e afins)
- [ ] Listar quais documentos fiscais entram em “afins”, além de CT-e e MDF-e
- [ ] Descrever em [[operacao]] campos, estados, regras e telas de cada conjunto
- [ ] Implementar somente o que estiver escrito em [[operacao]] (e no [[kpis]], se for indicador)

## 11. O que falta para a finalização do escopo documentado

O LogiDash, no que está escrito nesta pasta, está finalizado quando for um gerador de painéis e uma ferramenta de visualização e acompanhamento de dados de transportadoras que:

- [ ] Ingere Excel/CSV ou SQL pela porta única, com Medallion, quarentena e linhagem
- [ ] Calcula os KPIs do dicionário vigente (exceto os bloqueados até o dicionário fechar o contrato)
- [ ] Renderiza painéis a partir de `DashboardSpec`, na stack do ADR-002, com isolamento entre clientes
- [ ] Permite visualizar e acompanhar os conjuntos descritos em [[operacao]] (cargas e emissões como documentos fiscais — CT-e, MDF-e e afins —, ainda sem contrato de campos)
- [ ] Mantém esta pasta como única fonte da verdade, com sincronia apenas após o ADR-005

Em 2026-11-11, Enzo decidiu que o sistema precisa ser completo, será usado para vendas, e que o recorte operacional é acompanhar dados (por enquanto, só cargas e emissões, sendo emissões documentos fiscais como CT-e e MDF-e), não um processo geral. O recorte visual do PR #2 não encerra o produto. O indicador de vendas já previsto no dicionário é só `frete_sobre_vendas`. Conjuntos, campos e indicadores novos entram nesta pasta antes do código.

Enquanto as [[pendencias]] e as questões em aberto dos ADRs não forem decididas — e enquanto [[operacao]] não descrever campos e telas — essas partes não entram no “pronto”, e o código não deve inventar a regra no lugar do dicionário.
