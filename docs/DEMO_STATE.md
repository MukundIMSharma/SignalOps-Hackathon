# Demo state

**Status:** targets from MASTER_PLAN §1 — not seeded, not verified.

## Scenario
NovaCommerce: inventory sync failure at Warehouse W1 for SKU-104. W2 holds enough stock to recover a subset.

## Deterministic counts (targets — fill exact numbers, then make seed.py match)
| Metric | Target | Seeded | Verified via API |
|---|---|---|---|
| Delayed orders linked to SKU-104 | 28 | – | – |
| Orders past expected dispatch date (subset of 28? decide) | 12 | – | – |
| Customers with delay tickets | 9 | – | – |
| VIP / high-priority customers | 4 | – | – |
| Affected customers (distinct) | TBD | – | – |
| Order value affected | TBD | – | – |
| W1 available SKU-104 | 0 | – | – |
| W2 available SKU-104 | TBD | – | – |
| Recoverable orders via W2 transfer | TBD | – | – |
| Unrecoverable after transfer | TBD | – | – |
| Sync failure timestamp | 2026-11-23T09:42:00 | – | – |

Overlapping counts are never added together in reports.

## Demo prompt
> Investigate all delayed orders. Identify the root cause, which customers are affected, the business impact, and what we should do next.

Cross-system questions:
- A: Which customers are affected by delayed orders caused by low stock, and have they raised support tickets?
- B: Which delayed orders can be fulfilled using inventory from another warehouse, and how many can we recover?
- C (optional): Prioritize the delayed orders based on SLA breach, customer tier, and complaints. Explain why each customer is prioritized.

## Commands
TBD (start APIs, reseed, start MCP servers, start backend/frontend, `synapse build --discover`).

## Rehearsals
| # | Date | Steps passed | Notes |
|---|---|---|---|
