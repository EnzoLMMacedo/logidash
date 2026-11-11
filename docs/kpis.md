---
id: kpis
titulo: Dicionário de KPIs Logísticos
status: Vigente
versao: 1.0.0
data: 2026-08-21
responsavel: Arquiteto
tags: [logidash, kpi, logistica, otif, frete, estoque, dicionario]
relacionados:
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[ADR-002-stack-renderizacao]]"
---

# Dicionário de KPIs Logísticos

Este documento é a **fonte da verdade** dos indicadores do LogiDash. Cada entrada aqui tem correspondência direta com um arquivo em `src/logidash/metrics/definitions/`, e o motor compila essas definições em SQL parametrizado contra o *star schema* da camada Gold.

Regra de governança: **nenhum KPI existe no código sem existir aqui primeiro.** Alterar uma fórmula exige incrementar a versão deste documento e registrar o motivo, porque mudança silenciosa de fórmula invalida comparações históricas.

---

## 1. Convenções

### 1.1 Campos canônicos

Nomes físicos de coluna variam entre clientes (`TRANSP`, `Transportadora`, `Carrier`). O `SemanticMapper` traduz o físico para os nomes canônicos abaixo, e **toda fórmula de KPI é escrita exclusivamente contra os canônicos**.

#### `fact_shipment` — grão: um embarque

| Campo canônico | Tipo | Nulo | Descrição |
| --- | --- | --- | --- |
| `shipment_id` | `string` | não | Identificador único do embarque |
| `tenant_id` | `string` | não | Cliente proprietário do dado |
| `carrier_id` | `string` | sim | Transportadora responsável |
| `origem_id` / `destino_id` | `string` | sim | Chaves para `dim_location` |
| `data_coleta` | `date` | sim | Data efetiva da coleta |
| `data_prometida_original` | `date` | **não** | Prazo prometido na emissão — base oficial de OTIF |
| `data_prometida_vigente` | `date` | sim | Prazo após renegociações |
| `data_entrega` | `date` | sim | Nulo enquanto não entregue |
| `qtd_pedida` | `int` | não | Quantidade solicitada pelo cliente |
| `qtd_expedida` | `int` | não | Quantidade que saiu do armazém |
| `qtd_entregue` | `int` | sim | Quantidade aceita no destino |
| `tentativas_entrega` | `int` | não | Número de tentativas, mínimo 1 |
| `peso_bruto_kg` | `decimal(18,4)` | sim | Peso real |
| `peso_cubado_kg` | `decimal(18,4)` | sim | Peso cubado pelo fator do modal |
| `volume_m3` | `decimal(18,4)` | sim | Cubagem |
| `distancia_km` | `decimal(18,4)` | sim | Distância percorrida |
| `status_final` | `string` | não | `ENTREGUE`, `EM_TRANSITO`, `DEVOLVIDO`, `EXTRAVIADO` |

#### `fact_tracking_event` — grão: um evento de rastreamento

| Campo canônico | Tipo | Nulo | Descrição |
| --- | --- | --- | --- |
| `shipment_id` | `string` | não | Embarque relacionado |
| `ocorrido_em` | `timestamp` | não | Momento do evento |
| `tipo_evento` | `string` | não | `COLETA`, `EM_TRANSITO`, `SAIU_ENTREGA`, `ENTREGUE`, `OCORRENCIA` |
| `codigo_ocorrencia` | `string` | sim | Chave para `dim_occurrence` |

#### `fact_freight` — grão: um embarque

| Campo canônico | Tipo | Nulo | Descrição |
| --- | --- | --- | --- |
| `shipment_id` | `string` | não | Embarque custeado |
| `valor_frete` | `decimal(18,4)` | não | Frete peso mais frete valor |
| `valor_pedagio` | `decimal(18,4)` | sim | Pedágio |
| `valor_gris_advalorem` | `decimal(18,4)` | sim | GRIS e ad valorem |
| `valor_mercadoria` | `decimal(18,4)` | sim | Valor da nota fiscal |
| `valor_cotado` | `decimal(18,4)` | sim | Valor previsto na tabela contratada |

#### `fact_inventory` — grão: SKU por armazém por dia (*snapshot*)

| Campo canônico | Tipo | Nulo | Descrição |
| --- | --- | --- | --- |
| `data_snapshot` | `date` | não | Data da fotografia do estoque |
| `sku` | `string` | não | Item |
| `location_id` | `string` | não | Armazém |
| `qtd_disponivel` | `decimal(18,4)` | não | Saldo disponível |
| `qtd_contada` | `decimal(18,4)` | sim | Saldo apurado em inventário físico |
| `custo_unitario` | `decimal(18,4)` | sim | Custo médio unitário |
| `demanda_media_diaria` | `decimal(18,4)` | sim | Média móvel de consumo |

#### `dim_occurrence` — classificação de ocorrências

| Campo canônico | Tipo | Descrição |
| --- | --- | --- |
| `codigo` | `string` | Código da ocorrência |
| `culpa_transportadora` | `bool` | Se a responsabilidade é do transportador |
| `impacta_otif` | `bool` | Se penaliza o indicador de nível de serviço |

### 1.2 Regra de agregação — a convenção mais importante deste documento

Todo KPI declara uma **classe de agregação**, e o motor obedece a ela ao mudar de granularidade. Ignorar isso é a origem mais comum de números errados em BI logístico.

| Classe | Comportamento | Exemplos |
| --- | --- | --- |
| `aditivo` | Soma livremente em qualquer dimensão | Custo total de frete, km rodado |
| `razao_de_somas` | **Não aditivo.** Recalcular somando numerador e denominador separadamente | OTIF, pontualidade, ruptura |
| `media_ponderada` | Média com peso explícito declarado | Custo por kg, lead time médio |
| `semi_aditivo` | Soma entre entidades, **nunca** ao longo do tempo | Saldo de estoque |

O erro clássico: OTIF geral **não** é a média dos OTIF por transportadora. Uma transportadora com 2 embarques a 50% e outra com 998 embarques a 99% dão média simples de 74,5%, quando o real é 98,9%. A classe `razao_de_somas` existe justamente para impedir isso.

O caso `semi_aditivo` é igualmente traiçoeiro: somar o saldo de estoque de trinta *snapshots* diários produz um número trinta vezes maior que a realidade. Estoque agrega entre SKUs e armazéns, mas ao longo do tempo só admite média ou último valor.

### 1.3 Convenções de escrita das fórmulas

- Parâmetros sempre nomeados (`:inicio`, `:fim`), **jamais** interpolados em string — ver [[ADR-002-stack-renderizacao]].
- Toda divisão protegida por `NULLIF(denominador, 0)`.
- Percentuais expressos como fração decimal entre 0 e 1; a formatação é responsabilidade do frontend.
- Filtro de tenant injetado pelo motor, nunca escrito na definição.

---

## 2. Índice

| ID | Nome | Domínio | Unidade | Direção | Agregação |
| --- | --- | --- | --- | --- | --- |
| `otif` | OTIF | Entrega | fração | maior melhor | `razao_de_somas` |
| `otd` | Pontualidade (On Time) | Entrega | fração | maior melhor | `razao_de_somas` |
| `in_full` | Completude (In Full) | Entrega | fração | maior melhor | `razao_de_somas` |
| `lead_time_medio` | Lead Time Médio | Entrega | dias | menor melhor | `media_ponderada` |
| `desvio_prazo_dias` | Desvio de Prazo | Entrega | dias | menor melhor | `media_ponderada` |
| `first_attempt_rate` | Entrega na 1ª Tentativa | Entrega | fração | maior melhor | `razao_de_somas` |
| `taxa_ocorrencias` | Taxa de Ocorrências | Entrega | fração | menor melhor | `razao_de_somas` |
| `taxa_reentrega` | Taxa de Reentrega | Entrega | fração | menor melhor | `razao_de_somas` |
| `taxa_devolucao` | Taxa de Devolução | Entrega | fração | menor melhor | `razao_de_somas` |
| `frete_sobre_vendas` | Frete sobre Vendas | Frete | fração | menor melhor | `razao_de_somas` |
| `custo_por_km` | Custo por Km | Frete | R$/km | menor melhor | `razao_de_somas` |
| `custo_por_kg` | Custo por Kg | Frete | R$/kg | menor melhor | `razao_de_somas` |
| `custo_por_entrega` | Custo por Entrega | Frete | R$ | menor melhor | `media_ponderada` |
| `aderencia_tabela` | Aderência à Tabela | Frete | fração | menor melhor | `razao_de_somas` |
| `ocupacao_veiculo` | Ocupação do Veículo | Frete | fração | maior melhor | `razao_de_somas` |
| `giro_estoque` | Giro de Estoque | Estoque | vezes | maior melhor | `razao_de_somas` |
| `cobertura_dias` | Cobertura de Estoque | Estoque | dias | contexto | `media_ponderada` |
| `taxa_ruptura` | Ruptura (Stockout) | Estoque | fração | menor melhor | `razao_de_somas` |
| `acuracidade_inventario` | Acuracidade de Inventário | Estoque | fração | maior melhor | `razao_de_somas` |
| `fill_rate` | Fill Rate | Estoque | fração | maior melhor | `razao_de_somas` |

---

## 3. Domínio: Entrega e Transporte

### `otif` — OTIF (On Time In Full)

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,95 · **Grão** embarque · **Agregação** `razao_de_somas`

Percentual de embarques entregues **dentro do prazo prometido originalmente E com a quantidade completa**. É o indicador-síntese de nível de serviço logístico.

**Fórmula** — `entregas pontuais e completas ÷ embarques com prazo no período`

```sql
SELECT
    SUM(
        CASE
            WHEN s.data_entrega IS NOT NULL
             AND s.data_entrega <= s.data_prometida_original
             AND s.qtd_entregue >= s.qtd_pedida
            THEN 1 ELSE 0
        END
    )::DECIMAL / NULLIF(COUNT(*), 0) AS otif
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `data_prometida_original` (`date`), `data_entrega` (`date`, nulo permitido), `qtd_pedida` (`int`), `qtd_entregue` (`int`)

**Armadilhas**

O denominador filtra por **prazo prometido**, não por data de entrega. Filtrar por `data_entrega` remove silenciosamente os embarques nunca entregues — exatamente os piores casos — e infla o indicador.

Usar `data_prometida_vigente` no lugar da original transforma o KPI em ficção: bastaria reagendar toda entrega atrasada para exibir 100%. A comparação entre as duas datas é um indicador separado, de renegociação de prazo.

Entrega pontual porém incompleta **não** conta como OTIF. Essa é a confusão mais comum entre OTIF e pontualidade simples.

---

### `otd` — Pontualidade (On Time Delivery)

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,97 · **Grão** embarque · **Agregação** `razao_de_somas`

Componente temporal isolado do OTIF. Existe separadamente porque, quando o OTIF cai, a primeira pergunta é se o problema é de prazo ou de quantidade.

```sql
SELECT
    SUM(
        CASE
            WHEN s.data_entrega IS NOT NULL
             AND s.data_entrega <= s.data_prometida_original
            THEN 1 ELSE 0
        END
    )::DECIMAL / NULLIF(COUNT(*), 0) AS otd
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `data_prometida_original` (`date`), `data_entrega` (`date`)

**Armadilha** Sempre apresentar ao lado de `in_full`. Isoladamente, a pontualidade pode esconder um problema grave de completude.

---

### `in_full` — Completude (In Full)

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,98 · **Grão** embarque · **Agregação** `razao_de_somas`

Componente quantitativo isolado do OTIF.

```sql
SELECT
    SUM(CASE WHEN s.qtd_entregue >= s.qtd_pedida THEN 1 ELSE 0 END)::DECIMAL
        / NULLIF(COUNT(*), 0) AS in_full
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `qtd_pedida` (`int`), `qtd_entregue` (`int`)

**Armadilha** Medido por embarque, não por unidade. Um embarque com 99 de 100 peças conta como falha integral — comportamento correto do ponto de vista do cliente final, mas que precisa estar explícito para não gerar contestação.

---

### `lead_time_medio` — Lead Time Médio

**Unidade** dias · **Direção** menor melhor · **Grão** embarque · **Agregação** `media_ponderada` (peso: contagem de embarques)

Tempo decorrido entre a coleta e a entrega efetiva.

```sql
SELECT
    AVG(DATE_DIFF('day', s.data_coleta, s.data_entrega))::DECIMAL AS lead_time_medio,
    COUNT(*) AS peso_agregacao
FROM fact_shipment s
WHERE s.data_entrega IS NOT NULL
  AND s.data_coleta IS NOT NULL
  AND s.data_entrega >= s.data_coleta
  AND s.data_entrega BETWEEN :inicio AND :fim
```

**Campos exigidos** `data_coleta` (`date`), `data_entrega` (`date`)

**Armadilhas**

A média isolada é enganosa e **nunca deve ser exibida sozinha**. Ela esconde bimodalidade: "todo mundo leva 3 dias" e "90% leva 2 dias e 10% leva 15" produzem médias próximas e descrevem operações completamente diferentes. O painel deve exibir mediana e percentil 95 junto.

A cláusula `data_entrega >= data_coleta` não é defensiva por acaso — planilhas reais contêm datas invertidas, e sem esse filtro a média é puxada por valores negativos.

**Variação recomendada** Decompor por etapa usando `fact_tracking_event`, isolando tempo em armazém, tempo em trânsito e tempo até a primeira tentativa. É o que transforma o indicador em diagnóstico.

---

### `desvio_prazo_dias` — Desvio de Prazo

**Unidade** dias · **Direção** menor melhor · **Meta padrão** 0 · **Grão** embarque · **Agregação** `media_ponderada`

Diferença assinada entre entrega efetiva e prazo prometido. Negativo significa adiantamento.

```sql
SELECT
    AVG(DATE_DIFF('day', s.data_prometida_original, s.data_entrega))::DECIMAL
        AS desvio_prazo_dias,
    COUNT(*) AS peso_agregacao
FROM fact_shipment s
WHERE s.data_entrega IS NOT NULL
  AND s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `data_prometida_original` (`date`), `data_entrega` (`date`)

**Armadilha** Entregas adiantadas compensam atrasadas na média e podem zerar o indicador em uma operação instável. Este KPI deve ser renderizado como **histograma**, não como cartão numérico — a forma da distribuição é a informação, não a média.

---

### `first_attempt_rate` — Entrega na Primeira Tentativa

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,92 · **Grão** embarque · **Agregação** `razao_de_somas`

Percentual de entregas concluídas sem necessidade de nova visita. Impacta diretamente o custo por entrega.

```sql
SELECT
    SUM(CASE WHEN s.tentativas_entrega = 1 THEN 1 ELSE 0 END)::DECIMAL
        / NULLIF(COUNT(*), 0) AS first_attempt_rate
FROM fact_shipment s
WHERE s.status_final = 'ENTREGUE'
  AND s.data_entrega BETWEEN :inicio AND :fim
```

**Campos exigidos** `tentativas_entrega` (`int`), `status_final` (`string`)

**Armadilha** Muitos sistemas de origem não registram tentativas frustradas, gravando sempre `1`. A perfilagem deve alertar quando a cardinalidade de `tentativas_entrega` for igual a 1 — o indicador é inútil nesse caso e deve ser suprimido em vez de exibir 100%.

---

### `taxa_ocorrencias` — Taxa de Ocorrências

**Unidade** fração · **Direção** menor melhor · **Grão** embarque · **Agregação** `razao_de_somas`

Percentual de embarques com ao menos uma ocorrência que impacta nível de serviço.

```sql
SELECT
    COUNT(DISTINCT e.shipment_id)::DECIMAL
        / NULLIF((SELECT COUNT(*) FROM fact_shipment s2
                  WHERE s2.data_prometida_original BETWEEN :inicio AND :fim), 0)
        AS taxa_ocorrencias
FROM fact_tracking_event e
JOIN dim_occurrence o ON o.codigo = e.codigo_ocorrencia
JOIN fact_shipment s ON s.shipment_id = e.shipment_id
WHERE o.impacta_otif = TRUE
  AND s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `codigo_ocorrencia` (`string`), `impacta_otif` (`bool`), `data_prometida_original` (`date`)

**Armadilhas**

O `DISTINCT` é obrigatório: um embarque com quatro ocorrências conta uma vez, senão o indicador pode ultrapassar 100%.

O filtro `impacta_otif` é regra de negócio versionada, não detalhe técnico. Recusa do cliente na porta e avaria em trânsito não podem penalizar a transportadora do mesmo jeito. A classificação vive em `dim_occurrence` e mudá-la altera indicadores históricos — por isso é versionada.

---

### `taxa_reentrega` — Taxa de Reentrega

**Unidade** fração · **Direção** menor melhor · **Grão** embarque · **Agregação** `razao_de_somas`

```sql
SELECT
    SUM(CASE WHEN s.tentativas_entrega > 1 THEN 1 ELSE 0 END)::DECIMAL
        / NULLIF(COUNT(*), 0) AS taxa_reentrega
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `tentativas_entrega` (`int`)

**Armadilha** É o complemento operacional de `first_attempt_rate`, mas com denominador diferente (todos os embarques, não só os entregues). Os dois não somam 1, e isso precisa estar claro no painel.

---

### `taxa_devolucao` — Taxa de Devolução

**Unidade** fração · **Direção** menor melhor · **Grão** embarque · **Agregação** `razao_de_somas`

```sql
SELECT
    SUM(CASE WHEN s.status_final = 'DEVOLVIDO' THEN 1 ELSE 0 END)::DECIMAL
        / NULLIF(COUNT(*), 0) AS taxa_devolucao
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `status_final` (`string`)

**Armadilha** Devolução total e devolução parcial são fenômenos distintos com causas distintas. Se a fonte suportar, separar em dois indicadores.

---

## 4. Domínio: Custo de Frete

### `frete_sobre_vendas` — Frete sobre Vendas

**Unidade** fração · **Direção** menor melhor · **Meta padrão** 0,08 · **Grão** embarque · **Agregação** `razao_de_somas`

Percentual do faturamento consumido por transporte. É o indicador financeiro mais acompanhado pela diretoria em logística.

```sql
SELECT
    SUM(f.valor_frete + COALESCE(f.valor_pedagio, 0)
        + COALESCE(f.valor_gris_advalorem, 0))
        / NULLIF(SUM(f.valor_mercadoria), 0) AS frete_sobre_vendas
FROM fact_freight f
JOIN fact_shipment s ON s.shipment_id = f.shipment_id
WHERE s.data_coleta BETWEEN :inicio AND :fim
```

**Campos exigidos** `valor_frete`, `valor_pedagio`, `valor_gris_advalorem`, `valor_mercadoria` (todos `decimal(18,4)`)

**Armadilhas**

O numerador precisa incluir pedágio, GRIS e ad valorem. Considerar apenas `valor_frete` subestima o custo real em torno de 10 a 20% em operação rodoviária brasileira.

`COALESCE` nos acessórios é essencial: sem ele, um pedágio nulo anula a soma inteira daquela linha.

Comparar esse percentual entre empresas de setores diferentes não faz sentido — o valor saudável depende do valor agregado do produto.

---

### `custo_por_km` — Custo por Quilômetro

**Unidade** R$/km · **Direção** menor melhor · **Grão** embarque · **Agregação** `razao_de_somas`

```sql
SELECT
    SUM(f.valor_frete + COALESCE(f.valor_pedagio, 0))
        / NULLIF(SUM(s.distancia_km), 0) AS custo_por_km
FROM fact_freight f
JOIN fact_shipment s ON s.shipment_id = f.shipment_id
WHERE s.distancia_km > 0
  AND s.data_coleta BETWEEN :inicio AND :fim
```

**Campos exigidos** `valor_frete`, `valor_pedagio`, `distancia_km` (`decimal(18,4)`)

**Armadilha** Não é a média dos custos por km individuais — é a razão das somas. Rotas curtas têm custo por km altíssimo e distorceriam uma média simples. O filtro `distancia_km > 0` evita divisão por zero em linhas com distância não preenchida.

---

### `custo_por_kg` — Custo por Quilo Transportado

**Unidade** R$/kg · **Direção** menor melhor · **Grão** embarque · **Agregação** `razao_de_somas`

```sql
SELECT
    SUM(f.valor_frete + COALESCE(f.valor_pedagio, 0)
        + COALESCE(f.valor_gris_advalorem, 0))
        / NULLIF(SUM(GREATEST(s.peso_bruto_kg, COALESCE(s.peso_cubado_kg, 0))), 0)
        AS custo_por_kg
FROM fact_freight f
JOIN fact_shipment s ON s.shipment_id = f.shipment_id
WHERE s.data_coleta BETWEEN :inicio AND :fim
```

**Campos exigidos** `valor_frete`, `peso_bruto_kg`, `peso_cubado_kg` (`decimal(18,4)`)

**Armadilha** O denominador usa `GREATEST` entre peso real e peso cubado, porque a transportadora **cobra pelo maior dos dois**. Usar apenas o peso bruto superestima a eficiência em cargas volumosas e leves, que é justamente onde o custo escapa.

---

### `custo_por_entrega` — Custo Médio por Entrega

**Unidade** R$ · **Direção** menor melhor · **Grão** embarque · **Agregação** `media_ponderada` (peso: contagem)

```sql
SELECT
    SUM(f.valor_frete + COALESCE(f.valor_pedagio, 0)
        + COALESCE(f.valor_gris_advalorem, 0))
        / NULLIF(COUNT(DISTINCT f.shipment_id), 0) AS custo_por_entrega,
    COUNT(DISTINCT f.shipment_id) AS peso_agregacao
FROM fact_freight f
JOIN fact_shipment s ON s.shipment_id = f.shipment_id
WHERE s.data_coleta BETWEEN :inicio AND :fim
```

**Campos exigidos** `valor_frete`, `shipment_id`

**Armadilha** Sensível ao mix de rotas. Uma queda pode significar eficiência ou simplesmente mais entregas urbanas curtas no período. Sempre analisar segmentado por faixa de distância.

---

### `aderencia_tabela` — Aderência à Tabela de Frete

**Unidade** fração · **Direção** menor melhor (desvio) · **Meta padrão** 0,02 · **Grão** embarque · **Agregação** `razao_de_somas`

Desvio entre o frete cotado em contrato e o efetivamente faturado. Indicador de auditoria de frete, historicamente o que gera recuperação financeira mais rápida.

```sql
SELECT
    SUM(ABS(f.valor_frete - f.valor_cotado))
        / NULLIF(SUM(f.valor_cotado), 0) AS aderencia_tabela
FROM fact_freight f
JOIN fact_shipment s ON s.shipment_id = f.shipment_id
WHERE f.valor_cotado IS NOT NULL
  AND f.valor_cotado > 0
  AND s.data_coleta BETWEEN :inicio AND :fim
```

**Campos exigidos** `valor_frete`, `valor_cotado` (`decimal(18,4)`)

**Armadilha** O `ABS` é deliberado: cobrança a menor também é um desvio de processo e costuma virar cobrança retroativa depois. Um painel de auditoria deve exibir também a soma assinada, para separar o que é prejuízo do que é crédito.

---

### `ocupacao_veiculo` — Ocupação do Veículo

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,85 · **Grão** veículo por viagem · **Agregação** `razao_de_somas`

```sql
SELECT
    SUM(GREATEST(
        s.peso_bruto_kg / NULLIF(v.capacidade_peso_kg, 0),
        COALESCE(s.volume_m3, 0) / NULLIF(v.capacidade_volume_m3, 0)
    )) / NULLIF(COUNT(*), 0) AS ocupacao_veiculo
FROM fact_shipment s
JOIN dim_vehicle v ON v.veiculo_id = s.veiculo_id
WHERE s.data_coleta BETWEEN :inicio AND :fim
```

**Campos exigidos** `peso_bruto_kg`, `volume_m3`, `capacidade_peso_kg`, `capacidade_volume_m3` (`decimal(18,4)`)

**Armadilha** A ocupação real é o **maior** entre a restrição de peso e a de cubagem, porque o veículo enche pelo que estourar primeiro. Medir só por peso faz uma carreta cheia de almofadas parecer vazia.

---

## 5. Domínio: Estoque e Armazém

### `giro_estoque` — Giro de Estoque

**Unidade** vezes no período · **Direção** maior melhor · **Grão** SKU por armazém · **Agregação** `razao_de_somas`

Quantas vezes o estoque foi integralmente renovado no período.

```sql
WITH estoque_medio AS (
    SELECT sku, location_id,
           AVG(qtd_disponivel * COALESCE(custo_unitario, 0)) AS valor_medio
    FROM fact_inventory
    WHERE data_snapshot BETWEEN :inicio AND :fim
    GROUP BY sku, location_id
),
custo_saidas AS (
    SELECT sku, location_id, SUM(qtd * custo_unitario) AS cmv
    FROM fact_inventory_movement
    WHERE tipo_movimento = 'SAIDA'
      AND data_movimento BETWEEN :inicio AND :fim
    GROUP BY sku, location_id
)
SELECT SUM(c.cmv) / NULLIF(SUM(e.valor_medio), 0) AS giro_estoque
FROM custo_saidas c
JOIN estoque_medio e ON e.sku = c.sku AND e.location_id = c.location_id
```

**Campos exigidos** `qtd_disponivel`, `custo_unitario` (`decimal(18,4)`), `data_snapshot` (`date`), movimentos de saída

**Armadilhas**

O denominador é o estoque **médio** do período, não o saldo final. Usar o saldo final produz um giro que oscila com o dia do fechamento.

O numerador é custo das saídas, não receita de vendas. Misturar preço de venda com custo de estoque infla o giro pela margem.

Nunca somar `qtd_disponivel` ao longo do tempo — é campo `semi_aditivo`, ver seção 1.2.

---

### `cobertura_dias` — Cobertura de Estoque

**Unidade** dias · **Direção** contexto (nem alto nem baixo é bom) · **Grão** SKU por armazém · **Agregação** `media_ponderada`

Por quantos dias o saldo atual atende a demanda média.

```sql
SELECT
    SUM(i.qtd_disponivel) / NULLIF(SUM(i.demanda_media_diaria), 0) AS cobertura_dias
FROM fact_inventory i
WHERE i.data_snapshot = :data_referencia
  AND i.demanda_media_diaria > 0
```

**Campos exigidos** `qtd_disponivel`, `demanda_media_diaria` (`decimal(18,4)`), `data_snapshot` (`date`)

**Armadilhas**

Item com demanda zero produz divisão por zero e precisa ser tratado como categoria separada — estoque obsoleto —, não como cobertura infinita.

A direção do indicador é contextual: cobertura baixa é risco de ruptura, cobertura alta é capital imobilizado. O painel deve exibir faixa-alvo, não uma seta de "melhor".

Usa `data_referencia` (um *snapshot*) em vez de intervalo, coerente com a natureza semi-aditiva do estoque.

---

### `taxa_ruptura` — Ruptura (Stockout)

**Unidade** fração · **Direção** menor melhor · **Meta padrão** 0,02 · **Grão** SKU por armazém por dia · **Agregação** `razao_de_somas`

```sql
SELECT
    SUM(CASE WHEN i.qtd_disponivel <= 0 THEN 1 ELSE 0 END)::DECIMAL
        / NULLIF(COUNT(*), 0) AS taxa_ruptura
FROM fact_inventory i
WHERE i.data_snapshot BETWEEN :inicio AND :fim
```

**Campos exigidos** `qtd_disponivel` (`decimal(18,4)`), `data_snapshot` (`date`)

**Armadilha** Medida em SKU-dia, não em SKU. Um item em falta por vinte dias pesa vinte vezes mais que um em falta por um dia, que é o comportamento correto. Ponderar por relevância comercial (curva ABC) evita que itens de cauda longa dominem o indicador.

---

### `acuracidade_inventario` — Acuracidade de Inventário

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,98 · **Grão** SKU por armazém · **Agregação** `razao_de_somas`

```sql
SELECT
    1 - (SUM(ABS(i.qtd_contada - i.qtd_disponivel))
         / NULLIF(SUM(i.qtd_disponivel), 0)) AS acuracidade_inventario
FROM fact_inventory i
WHERE i.qtd_contada IS NOT NULL
  AND i.data_snapshot BETWEEN :inicio AND :fim
```

**Campos exigidos** `qtd_contada`, `qtd_disponivel` (`decimal(18,4)`)

**Armadilha** Usa valor absoluto por SKU. Sem o `ABS`, uma sobra de 100 em um item cancela uma falta de 100 em outro e o armazém aparenta acuracidade perfeita enquanto tem dois erros graves.

---

### `fill_rate` — Fill Rate

**Unidade** fração · **Direção** maior melhor · **Meta padrão** 0,97 · **Grão** embarque · **Agregação** `razao_de_somas`

Percentual da quantidade pedida que foi efetivamente atendida.

```sql
SELECT
    SUM(LEAST(s.qtd_expedida, s.qtd_pedida))::DECIMAL
        / NULLIF(SUM(s.qtd_pedida), 0) AS fill_rate
FROM fact_shipment s
WHERE s.data_prometida_original BETWEEN :inicio AND :fim
```

**Campos exigidos** `qtd_pedida`, `qtd_expedida` (`int`)

**Armadilha** Diferente de `in_full`, que é binário por embarque, o fill rate é proporcional por unidade. `LEAST` impede que uma expedição a maior compense faltas de outros pedidos e empurre o indicador acima de 100%.

---

## 6. Histórico de versões

| Versão | Data | Alteração |
| --- | --- | --- |
| 1.0.0 | 2026-08-21 | Versão inicial com 20 KPIs nos domínios de entrega, frete e estoque |
