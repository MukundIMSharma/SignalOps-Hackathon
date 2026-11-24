"""Integration: every Synapse MCP tool, called through MCP (needs both APIs running + SYNAPSE_API_KEY).

Counts mirror docs/DEMO_STATE.md.
"""
import asyncio
import json

from mcp_clients.servers import connect


async def call_all():
    out = {}
    async with connect("orders") as s:
        for name, args in [("get_delayed_orders", {}), ("get_at_risk_orders", {}), ("list_orders", {}),
                           ("get_order_details", {"order_id": "O-1026"}), ("get_order_details", {"order_id": "O-9999"}),
                           ("get_customer_details", {"customer_id": "C-1003"}),
                           ("get_customer_orders", {"customer_id": "C-1003"}), ("get_shipment_status", {}),
                           ("get_support_tickets", {}), ("get_order_health", {})]:
            r = await s.call_tool(name, args)
            out[(name, json.dumps(args))] = (r.is_error, json.loads(r.content[0].text))
    async with connect("inventory") as s:
        for name, args in [("list_products", {}), ("get_product_details", {"product_id": "SKU-104"}),
                           ("get_warehouse_inventory", {}), ("get_low_stock_products", {}),
                           ("get_product_stock", {"product_id": "SKU-104"}), ("get_warehouse_status", {}),
                           ("get_inventory_sync_status", {}), ("get_stock_health", {})]:
            r = await s.call_tool(name, args)
            out[(name, json.dumps(args))] = (r.is_error, json.loads(r.content[0].text))
    return out


R = asyncio.run(call_all())


def ok(name, **args):
    is_error, body = R[(name, json.dumps(args))]
    assert not is_error, body
    return body


def test_orders_tools():
    delayed = ok("get_delayed_orders")["items"]
    incident = [o for o in delayed if o["delay_reason"] == "stock_allocation_failed"]
    assert len(delayed) == 30 and len(incident) == 28
    assert sum(o["sla_breached"] for o in incident) == 12
    assert len({o["customer_id"] for o in incident}) == 24
    assert len(ok("get_at_risk_orders")["items"]) == 16
    orders = ok("list_orders")
    assert orders["total"] == len(orders["items"]) == 60  # full list in one call
    assert ok("get_order_details", order_id="O-1026")["delay_reason"] == "carrier_exception"
    assert ok("get_customer_details", customer_id="C-1003")["tier"] == "vip"
    assert ok("get_customer_orders", customer_id="C-1003")["total"] >= 2
    assert sum(s["status"] == "exception" for s in ok("get_shipment_status")["items"]) == 2
    tickets = ok("get_support_tickets")["items"]
    assert len({t["customer_id"] for t in tickets if t["category"] == "delivery_delay"}) == 9
    assert ok("get_order_health")["delayed_by_reason"]["stock_allocation_failed"] == 28


def test_orders_error_is_flagged():
    is_error, body = R[("get_order_details", json.dumps({"order_id": "O-9999"}))]
    assert is_error and body["error"]["code"] == "not_found"


def test_inventory_tools():
    assert ok("list_products")["total"] == 8
    assert ok("get_product_details", product_id="SKU-104")["reorder_threshold"] == 20
    assert ok("get_warehouse_inventory")["total"] == 16
    assert {(i["product_id"], i["warehouse_id"]) for i in ok("get_low_stock_products")["items"]} == {
        ("SKU-104", "W1"), ("SKU-107", "W2")}
    by_wh = {w["warehouse_id"]: w["available_quantity"] for w in ok("get_product_stock", product_id="SKU-104")["warehouses"]}
    assert by_wh == {"W1": 0, "W2": 60}
    assert {w["warehouse_id"]: w["status"] for w in ok("get_warehouse_status")["items"]}["W1"] == "degraded"
    failed = [s for s in ok("get_inventory_sync_status")["items"] if s["status"] == "failed"]
    assert len(failed) == 1 and failed[0]["failing_since"] == "2026-11-23T09:42:00"
    assert ok("get_stock_health")["failed_syncs"] == 1
