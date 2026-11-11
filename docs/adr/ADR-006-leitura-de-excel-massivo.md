---
id: ADR-006
titulo: Estratégia de leitura de Excel massivo
status: Aguarda benchmark
tags: [logidash, adr, aguarda-benchmark, excel, ingestao]
relacionados:
  - "[[ADR-001-ingestao-e-normalizacao]]"
  - "[[README]]"
  - "[[pendencias]]"
---

# ADR-006 — Estratégia de leitura de Excel massivo

## Status

**Aguarda benchmark.** Esta nota existe só para o índice e a navegação no vault. Ainda não há decisão registrada aqui.

O [[ADR-001-ingestao-e-normalizacao]] deixou em aberto o benchmark de leitura de Excel (comparar `python-calamine` e um leitor SAX em streaming, sobre um arquivo real de 200 MB, medindo tempo e pico de memória). O resultado deve fixar a implementação e ser registrado nesta ADR. Até o benchmark existir, a biblioteca de leitura não está escolhida.

Nada além do título, do status e dessa dependência já documentada no ADR-001 deve ser lido como regra nova.
