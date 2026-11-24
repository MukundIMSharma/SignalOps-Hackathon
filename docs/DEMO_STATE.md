# Demo state

**Status:** LOCKED (2026-11-24). Seeded in `nova-orders/app/seed.py` and `nova-inventory/app/seed.py`; "✓ pytest" = asserted by API tests against the seeded API.

## Scenario
NovaCommerce. At 2026-11-23T09:42:00 the W1 warehouse-management sync (source `W1-WMS`) started rejecting the SKU-104 payload. Since then W1 reports SKU-104 `available_quantity = 0` (last good update 09:41), so order allocation for SKU-104 at W1 fails and those orders sit in `delayed` with `delay_reason = stock_allocation_failed`. W2 has spare SKU-104 stock.

Two unrelated delayed orders (SKU-102, W2, carrier exception) exist so the agent has to *correlate* rather than assume every delay is the incident.

**Fixed clock:** `AS_OF = 2026-11-24T12:00:00` (env `DEMO_AS_OF`). SLA breach = not dispatched and `expected_dispatch_date < AS_OF`. No wall-clock time is used, so results never drift.

## Deterministic counts
| # | Metric | Value | Definition / overlap | Seeded | Verified |
|---|---|---|---|---|---|
| 1 | Total orders | 60 | | ✓ | ✓ pytest |
| 2 | Delayed orders (all causes) | 30 | status = delayed | ✓ | ✓ pytest |
| 3 | Delayed orders linked to incident | 28 | subset of #2: SKU-104, W1, stock_allocation_failed | ✓ | ✓ pytest |
| 4 | Delayed, unrelated | 2 | subset of #2: SKU-102, W2, carrier_exception | ✓ | ✓ pytest |
| 5 | Incident orders past dispatch date (SLA breached) | 12 | subset of #3 | ✓ | ✓ pytest |
| 6 | Incident orders at risk (not yet breached) | 16 | subset of #3; #5 + #6 = #3 | ✓ | ✓ pytest |
| 7 | Affected customers (distinct, incident) | 24 | 4 customers have 2 orders each (C-1003, C-1006, C-1011, C-1018) | ✓ | ✓ pytest |
| 8 | Affected VIP customers | 4 | subset of #7: C-1003, C-1008, C-1015, C-1021 (6 VIPs in system) | ✓ | ✓ pytest |
| 9 | Affected customers with delay tickets | 9 | subset of #7: C-1002, C-1003, C-1005, C-1008, C-1010, C-1013, C-1016, C-1019, C-1023 | ✓ | ✓ pytest |
| 10 | VIP ∩ ticket | 2 | C-1003, C-1008 | ✓ | by construction |
| 11 | Units on incident orders | 56 | quantities cycle 1,2,3,2 | ✓ | ✓ pytest |
| 12 | Order value affected | 7,224.00 | 56 × 129.00 (SKU-104 unit price) | ✓ | ✓ pytest |
| 13 | W1 SKU-104 available | 0 | stale since 2026-11-23T09:41:00 | ✓ | ✓ pytest |
| 14 | W2 SKU-104 available | 60 | reorder threshold 20 | ✓ | ✓ pytest |
| 15 | Transferable from W2 | 40 | available − reorder threshold (keep safety stock) | ✓ | ✓ pytest |
| 16 | Shortage after transfer | 16 units | 56 − 40 | ✓ | by construction |
| 17 | Recoverable orders via transfer | 20 | greedy in priority rank (agent/prioritization.py weights), skip orders that don't fit; uses all 40 units | ✓ | ✓ pytest |
| 18 | Unrecoverable after transfer | 8 | 28 − #17 | ✓ | ✓ pytest |
| 19 | Support tickets total | 11 | 9 delay (#9) + 2 unrelated (billing, product question) | ✓ | ✓ pytest |
| 20 | Customers total | 40 | | ✓ | ✓ pytest |

Never add overlapping rows (e.g. #5 + #9) in reports.

## Demo prompt
> Investigate all delayed orders. Identify the root cause, which customers are affected, the business impact, and what we should do next.

Cross-system questions:
- A: Which customers are affected by delayed orders caused by low stock, and have they raised support tickets?
- B: Which delayed orders can be fulfilled using inventory from another warehouse, and how many can we recover?
- C (optional): Prioritize the delayed orders based on SLA breach, customer tier, and complaints. Explain why each customer is prioritized.

## Commands
```powershell
powershell -File scripts\start-demo.ps1 -Reset   # reseed + start all 4 + wait for health
python scripts\rehearse.py 5                     # automated end-to-end check
```
Manual equivalents:
```bash
# reseed (deterministic)
cd nova-orders && .venv/Scripts/python -m app.seed
cd nova-inventory && .venv/Scripts/python -m app.seed
# run
cd nova-orders && .venv/Scripts/python -m uvicorn app.main:app --port 8001
cd nova-inventory && .venv/Scripts/python -m uvicorn app.main:app --port 8002
```
```bash
# terminal investigation through both Synapse MCP servers (verified 2026-11-24)
cd signalops-backend && .venv/Scripts/python investigate.py
```
```bash
cd signalops-backend  && .venv/Scripts/python -m uvicorn main:app --port 8000
cd signalops-frontend && npm run dev        # open http://localhost:5173
```
Live discovery step: follow `docs/live-endpoint.md` exactly (paste-ready code + commands + reset).

## Rehearsals
| # | Date | Steps passed | Notes |
|---|---|---|---|
| 1 | 2026-11-24 | M6 discovery only: endpoint added from docs/live-endpoint.md → restart → `synapse build --discover` (3.7s, same server_id) → Systems shows ★ newly discovered (8→9 tools) → investigation shows ★ New capability + evidence INV-2026-042 → reset to 8 tools | passed; screenshots in docs/demo-backup/ |
| 2 | 2026-11-24 | `scripts/rehearse.py 5` on a fresh stack: 5 investigations (3.0–4.3s, 30 MCP calls each), all 12 impact numbers + root cause + cross-system evidence identical every run; approve → executed, duplicate → 409, audit complete, tool counts 9/8 | passed (0 failed checks) |
