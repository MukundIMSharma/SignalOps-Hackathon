# Synapse setup (only commands verified to work)

CLI: `@2ndbrainlabs-ai/synapse-cli` v0.1.9, Node v24.16.0.

```bash
npm install -g @2ndbrainlabs-ai/synapse-cli   # worked 2026-11-24
synapse --version                              # 0.1.9
```

Relevant `synapse build` flags (from `synapse build --help`, v0.1.9):
- `--auto` Auto track (HTTP endpoints via runner) — what Track 3 needs
- `--base-url <url>` deployed base URL of the API
- `--server-name <name>` MCP server name; rebuild with the same name updates it
- `--endpoints "<list>"` choose endpoints without the picker
- `--discover` rescan code instead of reusing last build's endpoints (live demo step)
- `--smart-names` name tools from handler source
- `--local --provider ... --model ...` build on your own model instead of hosted

API key: `synapse config set-key` (prompts, keeps key out of shell history). Not done yet.

## Verified 2026-11-24
```bash
synapse config set-key --global          # run in a normal terminal; interactive prompt
cd nova-orders    && synapse -y init     # reuses global key; writes .synapse/config.json (gitignored: holds encrypted key)
synapse -y build --auto --discover --server-name nova-orders --base-url http://localhost:8001 \
  --endpoints "get_delayed_orders,get_at_risk_orders,get_order_details,get_customer_details,get_customer_orders,get_shipment_status,get_support_tickets,get_order_health,list_orders"
# -> server_id 6ab65632-0790-4e06-8b0e-77bb3d448920 (session sess_33212839_mwu81gu6_de066d)
cd nova-inventory && synapse -y init
synapse -y build --auto --server-name nova-inventory --base-url http://localhost:8002 \
  --endpoints "list_products,get_product_details,get_warehouse_inventory,get_low_stock_products,get_product_stock,get_warehouse_status,get_inventory_sync_status,get_stock_health"
# -> server_id bf451b7a-95c9-4658-b2a6-91708fb7ef84 (session sess_33212839_mwu81rd9_d935bf)
```

Gotchas:
- **Scanner ignores `APIRouter(prefix=...)` and skips `@router.get("")`.** First build detected `/delayed`, `/{order_id}` etc. Fix: full path in every decorator, no router prefix.
- `--endpoints` accepts tool names = FastAPI operationIds (we set operationId = function name). `/health` deliberately not exposed.
- Generated MCP runs **locally** over stdio: `npx -y @2ndbrainlabs-ai/synapse-mcp` with env `SYNAPSE_SERVER_ID`, `SYNAPSE_API_KEY`, `ENDPOINT_BASE_URL`. So localhost APIs work; the runner refuses to start without `SYNAPSE_API_KEY` in env.
- `.synapse/` besides `config.json` (discover logs, surface_cache) has no secrets and is committed.
- Tool descriptions come from handler **docstrings**, not FastAPI `summary=`.
- **No query params in tool schemas** (path params only), even with `--smart-names`. See KNOWN_ISSUES.
- Rebuild after code changes: same `--server-name` + `--discover` keeps the same server_id (verified).

Verify both servers (APIs running, SYNAPSE_API_KEY in .env):
```bash
cd signalops-backend
.venv/Scripts/python list_tools.py
.venv/Scripts/python -m pytest -q tests/test_mcp_tools.py   # 3 passed
```
- **Install the MCP runner globally:** `npm install -g @2ndbrainlabs-ai/synapse-mcp` (v0.0.4). Session start drops from 9–20s (`npx -y` registry check) to ~2s for both servers. `mcp_clients/servers.py` uses `synapse-mcp` if on PATH, else npx.
