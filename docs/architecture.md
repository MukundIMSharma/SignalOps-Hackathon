# Architecture

```mermaid
sequenceDiagram
  participant U as Operator (UI)
  participant B as signalops-backend
  participant O as Orders MCP (Synapse)
  participant I as Inventory MCP (Synapse)
  participant G as Gemini (optional)
  U->>B: POST /api/investigations
  B-->>U: SSE: stage / tool_call / evidence events
  B->>O: get_delayed_orders, get_support_tickets, get_shipment_status
  B->>I: get_inventory_sync_status, get_warehouse_status [, get_inventory_incidents if discovered]
  Note over B: correlate SKU + warehouse + timing (code)
  B->>I: get_product_stock(SKU-104)
  B->>O: get_customer_details(C-…) ×24
  Note over B: impact, ranking, transfer allocation, actions (code)
  B-->>U: report (status awaiting_approval)
  B->>G: findings JSON → executive summary
  G-->>B: text (or timeout → labelled template)
  U->>B: approve A-001
  B->>I: get_product_stock (re-validate)
  B-->>U: executed (simulated) + audit entry
```

## Principles → where they live
| Principle (plan §1) | Implementation |
|---|---|
| Synapse essential, visible | All business reads go through `mcp_clients/servers.py` (stdio sessions to `synapse-mcp`); Systems page lists tools per server; activity feed tags every call with its server |
| Separate codebases | `nova-orders`, `nova-inventory`: own app, venv, SQLite, seed, tests |
| Evidence for every finding | `agent/orchestrator.py` `add_evidence()`; findings reference evidence IDs; UI links them |
| Deterministic calculations | `agent/correlation.py`, `impact.py`, `prioritization.py` — no LLM |
| Facts vs hypotheses vs unknowns | Finding status `confirmed / likely / hypothesis / unknown` with a written reason |
| Partial, labelled reports | Tool failures → `gaps[]`, status `partial`; tested for each system down, truncation, retries, call budget |
| Human approval | `services/approvals.py`: re-validate via MCP, simulated ledger, one decision per action, audit JSONL |
| Repeatable demo | Deterministic seeds + fixed clock; `scripts/rehearse.py` checks every number |

## Bounds and safety
- Tool calls: budget 60 per investigation, 20 s timeout each, 1 retry (read-only tools only).
- Sessions are opened per request (~2 s with the global `synapse-mcp` install), so `synapse build --discover` changes are picked up without restarting.
- The LLM sees only the finished findings JSON and is instructed not to add facts; its output is labelled with its source.

Contracts: [CONTRACTS.md](CONTRACTS.md). Decisions and their reasons: [DECISIONS.md](DECISIONS.md).
