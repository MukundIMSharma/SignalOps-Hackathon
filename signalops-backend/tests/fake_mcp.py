"""Replays the seeded snapshot as MCP tool results; lets tests knock out a server or tool."""
import copy
import json
import pathlib

from agent.orchestrator import ToolError

SNAP = json.loads((pathlib.Path(__file__).parent / "fixtures" / "seed_snapshot.json").read_text())


def page(items):
    return {"items": items, "total": len(items), "limit": 200, "offset": 0, "as_of": SNAP["as_of"]}


def fake_call(snap=None, down: set[str] = frozenset(), broken_tools: set[str] = frozenset()):
    s = copy.deepcopy(snap or SNAP)
    calls = []

    async def call(server, tool, args):
        calls.append((server, tool, args))
        if server in down or tool in broken_tools:
            raise ToolError(f"{server} MCP unavailable")
        match tool:
            case "get_delayed_orders": return page(s["delayed_orders"])
            case "get_support_tickets": return page(s["tickets"])
            case "get_shipment_status": return page(s["shipments"])
            case "get_customer_details":
                if args["customer_id"] not in s["customers"]:
                    raise ToolError(f"get_customer_details: Customer {args['customer_id']} not found")
                return s["customers"][args["customer_id"]]
            case "get_inventory_sync_status": return page(s["sync_status"])
            case "get_warehouse_status": return page(s["warehouses"])
            case "get_product_stock": return s["product_stock_SKU-104"]
        raise AssertionError(f"unexpected tool {tool}")

    call.calls = calls
    return call
