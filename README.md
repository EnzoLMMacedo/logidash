# logidash

Gerador de painéis logísticos multi-cliente. As regras de negócio estão em [`docs/README.md`](docs/README.md).

Este recorte entrega o motor de KPI: OTIF sobre `fact_shipment`, quarentena de contrato e o SqlGuard. O painel no navegador fica para um recorte seguinte.

## Testes

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Os testes usam fixtures canônicas em memória. Não há leitura de planilha nem banco externo.
