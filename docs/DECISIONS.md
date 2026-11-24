# Decisions

Format: `date — decision — reason`

- 2026-11-24 — Monorepo `signalops/` with independently runnable `nova-orders/`, `nova-inventory/`, `signalops-backend/`, `signalops-frontend/` — plan §6, hackathon speed; split repos only if Synapse scanning requires it.
- 2026-11-24 — Project memory lives in plain markdown (CLAUDE.md + docs/) — Claude Code reads CLAUDE.md every session; it points at the rest.
- 2026-11-24 — Fixed demo clock `DEMO_AS_OF=2026-11-24T12:00:00` for SLA math — wall-clock time would make counts drift between rehearsals.
- 2026-11-24 — Support tickets live in the Orders system (`GET /tickets`) — question A needs them; Orders already owns customers; no third system needed for P0.
- 2026-11-24 — Seed includes 2 unrelated carrier-exception delays (30 delayed total, 28 incident) — forces real correlation instead of "every delay = incident".
- 2026-11-24 — Orders carry `delay_reason`; SyncStatus carries `warehouse_id` and `failing_since` (not in plan field list) — needed as source evidence for cause and timestamp.
- 2026-11-24 — Transferable W2 stock = available − reorder threshold (60 − 20 = 40) — keep safety stock; gives a realistic 16-unit residual shortage.
- 2026-11-24 — W1 warehouse status = `degraded` — warehouse API should corroborate the sync failure.
- 2026-11-24 — operationId = route function name = intended MCP tool name — so Synapse-generated tools get readable names.
- 2026-11-24 — Skipped optional `lifetime_value` (Customer) and `unit_price` (Product) — plan marks optional; Orders is source of order value.
- 2026-11-24 — Python 3.14 + FastAPI 0.165 / SQLAlchemy 2.1.9 / Pydantic 2.14.4, one venv per API — installed versions, keeps systems independent.
- 2026-11-24 — LLM = Google Gemini Flash (free tier), via `GEMINI_API_KEY` — user choice; model id to verify before use.
- 2026-11-24 — Full paths in route decorators, no router prefixes — Synapse v0.1.9 scanner ignores prefixes (would generate tools hitting wrong paths).
- 2026-11-24 — Backend MCP client package is `signalops-backend/mcp_clients/`, not `mcp/` as in plan §6 — a local `mcp` package would shadow the `mcp` SDK.
- 2026-11-24 — `/health` not exposed as MCP tool — health checks use direct HTTP per plan §5.
