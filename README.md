# logidash

Gerador de painéis logísticos multi-cliente. As regras de negócio estão em [`docs/README.md`](docs/README.md).

O motor de KPI calcula OTIF sobre `fact_shipment`. Este corte visual mostra o resultado e a quarentena numa página, com a API em memória. Não há banco para instalar.

## Subir a vista local

Em um terminal:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn logidash.api.aplicacao:app --host 127.0.0.1 --port 8000
```

Em outro:

```bash
cd web
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000). A tela mostra o OTIF do período 01/01/2026 a 31/01/2026 e as linhas que não entram na métrica.

Tokens de demonstração: `token-a` e `token-b`. O tenant sai do token. A tela não tem campo de tenant.

## Testes

```bash
pip install -e ".[dev]"
pytest
cd web && npm run build
```

Os testes da API usam o cliente HTTP em memória. Não há planilha nem banco.
