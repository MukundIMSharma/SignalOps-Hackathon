# Contracts

**Status:** DRAFT from MASTER_PLAN §7–§10. Nothing here is implemented or verified yet. Mark each section `LOCKED` once agreed; change it only together with the code.

## Orders API (`nova-orders`) — DRAFT
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/orders` | List; filter by status, priority, sku, date, warehouse; paginated |
| GET | `/orders/{order_id}` | Order detail |
| GET | `/orders/delayed` | Delayed orders |
| GET | `/orders/at-risk` | Orders likely to breach SLA |
| GET | `/customers/{customer_id}` | Customer details |
| GET | `/customers/{customer_id}/orders` | Customer history |
| GET | `/shipments` | Shipment list/filter |
| GET | `/analytics/order-health` | Summary statistics |

Entities:
- **Order:** order_id, customer_id, product_id, quantity, order_date, expected_dispatch_date, status, priority, unit_price, total_amount, warehouse_id, shipment_id (nullable)
- **Customer:** customer_id, name, tier (standard|vip), contact_preference, priority_flag
- **Shipment:** shipment_id, order_id, carrier, status, created_at, expected_delivery, actual_delivery (nullable), tracking_status

Open: where support tickets live (Orders field vs. separate dataset) — decide and record in DECISIONS.md.

## Inventory API (`nova-inventory`) — DRAFT
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/products` | Product catalog |
| GET | `/products/{product_id}` | Product details |
| GET | `/stock` | Stock query/filter |
| GET | `/stock/low` | Low stock |
| GET | `/stock/{product_id}` | Stock across warehouses |
| GET | `/warehouses` | Warehouse status |
| GET | `/sync/status` | Sync status |
| GET | `/analytics/stock-health` | Stock metrics |

Reserved for Milestone 6 live demo — **do not implement before then:** `GET /inventory/incidents`
```json
{ "incident_id": "INV-2026-042", "severity": "critical", "product_id": "SKU-104", "warehouse_id": "W1",
  "incident_type": "inventory_sync_failure", "occurred_at": "2026-11-23T09:42:00",
  "description": "Inventory synchronization failed; availability may be stale." }
```

Entities:
- **Product:** product_id, name, category, reorder_threshold, unit_price (optional)
- **Warehouse:** warehouse_id, name, location, status
- **Stock:** product_id, warehouse_id, available_quantity, reserved_quantity, last_updated
- **SyncStatus:** sync_id, source, status, last_attempt, last_success, error_code, error_message, affected_products, severity

## MCP tool names — PROPOSED (replace with the names Synapse actually generates)
| Server | Tool | Endpoint |
|---|---|---|
| orders | get_delayed_orders | `/orders/delayed` |
| orders | get_order_details | `/orders/{order_id}` |
| orders | get_customer_details | `/customers/{customer_id}` |
| orders | get_customer_orders | `/customers/{customer_id}/orders` |
| orders | get_shipment_status | `/shipments` |
| orders | get_order_health | `/analytics/order-health` |
| inventory | get_product_stock | `/stock/{product_id}` |
| inventory | get_low_stock_products | `/stock/low` |
| inventory | get_warehouse_inventory | `/stock` |
| inventory | get_warehouse_status | `/warehouses` |
| inventory | get_inventory_sync_status | `/sync/status` |
| inventory | get_stock_health | `/analytics/stock-health` |

## Evidence schema — DRAFT
```json
{
  "evidence_id": "E-001",
  "claim": "SKU-104 has insufficient available stock in W1",
  "status": "confirmed",
  "source_system": "inventory",
  "source_tool": "get_product_stock",
  "source_endpoint": "/stock/SKU-104",
  "entity_ids": ["SKU-104", "W1"],
  "observed_at": "2026-11-23T09:42:00",
  "data": { "available_quantity": 0 }
}
```
`status`: confirmed | likely | hypothesis | unknown

## Finding schema — DRAFT
finding_id, title, summary, severity, status (confirmed|likely|hypothesis|unknown), evidence_ids[], confidence_explanation (no pseudo-precise percentages), impact_metrics{}

## Investigation status — DRAFT
queued | investigating | partial | awaiting_approval | completed | failed | cancelled

## Approval payload — DRAFT
action_id, action_type, description, inputs, affected_entities[], risk_level, evidence_ids[], expected_outcome, approval_status, approver_id, timestamp, idempotency_key, execution_result

## SignalOps backend API (for frontend) — TBD
Define before Milestone 4 frontend work starts.
