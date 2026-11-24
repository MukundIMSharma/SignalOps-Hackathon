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
- 2026-11-24 — Agent filters full lists in code instead of passing filters to tools — Synapse v0.1.9 Auto passes path params only; filtering in code is deterministic anyway (plan §10).
- 2026-11-24 — Route docstrings = summaries — Synapse reads docstrings (not `summary=`) for tool descriptions.
- 2026-11-24 — Priority weights: VIP 30, SLA breached 25 + 5/day overdue (cap 3), open complaint 20, at-risk 10; order value not scored — plan §11 (transparent rules, don't penalise low-value customers); ties by dispatch date then order_id.
- 2026-11-24 — Transfer allocation: greedy in priority order, skip orders that don't fit — keeps priority meaningful and still uses all 40 units (20 recovered).
- 2026-11-24 — Backend unit tests run on a JSON snapshot of the seeded APIs (tests/fixtures) — fast/offline; MCP integration test covers the live path.
- 2026-11-24 — Root cause reported as `likely`, never `confirmed` — every fact is confirmed at source, but causality is inferred and W1's physical stock is unknown (stale). Plan principle 5.
- 2026-11-24 — Orchestrator takes an injected `call(server, tool, args)` — tests replay the snapshot and simulate outages without MCP; live uses `open_caller()`.
- 2026-11-24 — Skipped LLM intent parsing / query planning — the workflow is fixed and answers questions A/B/C from one report; add only if a free-form follow-up is demoed.
- 2026-11-24 — LLM_FALLBACK_MODEL=gemini-3.5-flash — 3.8-flash returned 503 repeatedly on free tier.
- 2026-11-24 — New MCP sessions per request (investigation, overview, systems), runner installed globally (~2s) — no connection state to manage, and tools added by `synapse build --discover` appear without restarting the backend.
- 2026-11-24 — Overview data also via MCP (not direct HTTP) — keeps the "business data only through Synapse" rule simple; direct HTTP only in /api/systems health checks.
- 2026-11-24 — Report published before the LLM summary (`narrative.source: pending`) — Gemini free tier can take ~60s.
- 2026-11-24 — Frontend uses Tailwind v4 with small hand-written components instead of the shadcn/ui CLI — same look (shadcn is copy-in Tailwind code), no Radix dependency tree, nothing interactive enough yet to need it.
- 2026-11-24 — Charts follow the dataviz skill's reference palette (dark series blue #3987e5, fixed status colors with icon + text); only one single-series chart + one status split, so no categorical palette to validate.
- 2026-11-24 — Cross-system questions A/B/C answered in a panel derived from the same report — the workflow is fixed; one run answers all three with evidence from both systems.
- 2026-11-24 — Actions execute against an in-memory simulated ledger, never the business APIs — plan §12 demo-safe actions; MCP tools stay read-only.
- 2026-11-24 — Approval re-validates via MCP at execution time and counts earlier simulated transfers — a stale plan or a second investigation can't over-commit W2 stock.
- 2026-11-24 — Idempotency = one decision per `{investigation}:{action}`; status flips before any await, so no lock is needed.
- 2026-11-24 — Audit log is append-only JSONL on disk — survives restarts even though investigations are in memory.
- 2026-11-24 — Agent calls `get_inventory_incidents` only if the MCP server lists it — before discovery a blind call would turn every report "partial"; after discovery it is used automatically with no backend restart.
- 2026-11-24 — Incident endpoint derives incidents from failed SyncStatus rows (no new table) — two small edits to paste live; output matches the plan's illustrative JSON exactly.
