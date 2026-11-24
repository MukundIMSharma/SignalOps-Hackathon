# Contracts

Business APIs are **LOCKED as implemented** (2026-11-24, Milestone 1, tests passing). Agent-side schemas are DRAFT until Milestone 3. Change a contract only together with the code and its tests.

## Common conventions (both APIs)
- `operationId` = Python function name = intended MCP tool name.
- List responses: `{ items: [...], total, limit, offset, as_of }`.
- Errors: `{ "error": { "code": "not_found" | "validation_error" | "http_error", "message": "..." } }` with 404 / 422.
- Fixed demo clock `as_of` = `DEMO_AS_OF` (default `2026-11-24T12:00:00`). Timestamps are naive ISO-8601, demo-local.
- `GET /health` → `{ status: "ok", service, as_of }`.

## Orders API (`nova-orders`, port 8001) — LOCKED
| Method | Endpoint | operationId | Filters / params |
|---|---|---|---|
| GET | `/health` | health | |
| GET | `/orders` | list_orders | status, priority, product_id, warehouse_id, customer_id, order_date_from, order_date_to, limit (1–200, default 50), offset |
| GET | `/orders/delayed` | get_delayed_orders | product_id, warehouse_id, delay_reason, limit (default 100), offset |
| GET | `/orders/at-risk` | get_at_risk_orders | limit, offset — delayed, undispatched, dispatch date not yet passed |
| GET | `/orders/{order_id}` | get_order_details | |
| GET | `/customers/{customer_id}` | get_customer_details | |
| GET | `/customers/{customer_id}/orders` | get_customer_orders | limit, offset |
| GET | `/shipments` | get_shipment_status | order_id, status, carrier, limit, offset |
| GET | `/tickets` | get_support_tickets | customer_id, order_id, category, status, limit, offset |
| GET | `/analytics/order-health` | get_order_health | |

Entities:
- **Order:** order_id, customer_id, product_id, quantity, order_date, expected_dispatch_date, status (pending|processing|delayed|shipped|delivered|cancelled), delay_reason (stock_allocation_failed|carrier_exception|null), priority (normal|high), unit_price, total_amount, warehouse_id, shipment_id (nullable), **computed:** sla_breached (no shipment and expected_dispatch_date < as_of), days_overdue (whole days rounded up, 0 if not breached)
- **Customer:** customer_id, name, tier (standard|vip), contact_preference (email|phone|sms), priority_flag
- **Shipment:** shipment_id, order_id, carrier, status (in_transit|delivered|exception), created_at, expected_delivery, actual_delivery (nullable), tracking_status
- **SupportTicket:** ticket_id, customer_id, order_id (nullable), category (delivery_delay|billing|product_question), status (open|closed), subject, created_at
- **OrderHealth:** as_of, total_orders, by_status{}, delayed_orders, delayed_by_reason{}, sla_breached_orders, at_risk_orders, delayed_order_value (all delay causes), open_tickets, open_delay_tickets

## Inventory API (`nova-inventory`, port 8002) — LOCKED
| Method | Endpoint | operationId | Filters / params |
|---|---|---|---|
| GET | `/health` | health | |
| GET | `/products` | list_products | category, limit, offset |
| GET | `/products/{product_id}` | get_product_details | |
| GET | `/stock` | get_warehouse_inventory | product_id, warehouse_id, limit, offset |
| GET | `/stock/low` | get_low_stock_products | warehouse_id — available < reorder_threshold |
| GET | `/stock/{product_id}` | get_product_stock | |
| GET | `/warehouses` | get_warehouse_status | |
| GET | `/sync/status` | get_inventory_sync_status | status, warehouse_id |
| GET | `/analytics/stock-health` | get_stock_health | |

Entities:
- **Product:** product_id, name, category, reorder_threshold
- **Warehouse:** warehouse_id, name, location, status (operational|degraded|offline)
- **Stock:** product_id, warehouse_id, available_quantity, reserved_quantity, last_updated
- **LowStock:** Stock + reorder_threshold, shortfall
- **ProductStock:** product_id, reorder_threshold, total_available, total_reserved, warehouses[Stock], as_of
- **SyncStatus:** sync_id, source, warehouse_id, status (success|failed), last_attempt, last_success, failing_since (nullable), error_code, error_message, affected_products[], severity (info|warning|critical)
- **StockHealth:** as_of, products, warehouses, warehouses_by_status{}, total_available_units, total_reserved_units, low_stock_positions, out_of_stock_positions, failed_syncs, products_affected_by_sync_failures[]

Reserved for Milestone 6 live demo — **not implemented, a test asserts it is absent:** `GET /inventory/incidents`
```json
{ "incident_id": "INV-2026-042", "severity": "critical", "product_id": "SKU-104", "warehouse_id": "W1",
  "incident_type": "inventory_sync_failure", "occurred_at": "2026-11-23T09:42:00",
  "description": "Inventory synchronization failed; availability may be stale." }
```

## MCP servers — BUILT (Milestone 2), tool calls not yet verified
| Server | server_id | Base URL | Exposed tools |
|---|---|---|---|
| nova-orders | 6ab65632-0790-4e06-8b0e-77bb3d448920 | http://localhost:8001 | all Orders operationIds except `health` |
| nova-inventory | bf451b7a-95c9-4658-b2a6-91708fb7ef84 | http://localhost:8002 | all Inventory operationIds except `health` |
Confirm exact generated tool names from `list_tools` and record them here.

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
  "observed_at": "2026-11-24T12:00:00",
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
