# Nova Inventory API

Independent NovaCommerce inventory system (FastAPI + SQLite). Part of SignalOps; see `../docs/CONTRACTS.md`.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows; use .venv/bin on macOS/Linux
.venv/Scripts/python -m app.seed                          # drop + reseed (deterministic)
.venv/Scripts/python -m uvicorn app.main:app --port 8002
.venv/Scripts/python -m pytest -q
```

- OpenAPI: http://localhost:8002/docs (operationIds = MCP tool names)
- Env: `INVENTORY_DATABASE_URL` (default `sqlite:///./inventory.db`), `DEMO_AS_OF` (default `2026-11-24T12:00:00`)
- Seeds automatically on first start if the database is empty.
