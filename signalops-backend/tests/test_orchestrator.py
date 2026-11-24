import asyncio
import copy

from agent.orchestrator import Investigation
from tests.fake_mcp import SNAP, fake_call


def run(call, **kw):
    return asyncio.run(Investigation(call, **kw).run())


def test_normal_incident():
    r = run(fake_call())
    assert r["status"] == "awaiting_approval" and r["gaps"] == []
    root = r["findings"][0]
    assert root["status"] == "likely" and "W1-WMS" in root["title"] and "SKU-104" in root["title"]
    ev = {e["evidence_id"]: e for e in r["evidence"]}
    assert all(i in ev for f in r["findings"] for i in f["evidence_ids"])  # no dangling evidence refs
    assert {ev[i]["source_system"] for i in root["evidence_ids"]} == {"orders", "inventory"}  # cross-system
    m = {k: v["value"] for k, v in r["impact"].items()}
    assert (m["incident_orders"], m["affected_customers"], m["recoverable_orders"]) == (28, 24, 20)
    assert len(r["priorities"]) == 28 and r["priorities"][0]["tier"] == "vip"
    assert any(f["title"].startswith("2 delayed orders not linked") and f["status"] == "confirmed" for f in r["findings"])
    transfer = next(a for a in r["actions"] if a["action_type"] == "inventory_transfer")
    assert transfer["inputs"] == {"product_id": "SKU-104", "source": "W2", "destination": "W1", "units": 40}
    assert transfer["requires_approval"] and transfer["approval_status"] == "pending"
    assert {s["server"] for s in r["trace"]} == {"orders", "inventory"}


def test_repeatable():
    a, b = run(fake_call()), run(fake_call())
    assert a["findings"] == b["findings"] and a["priorities"] == b["priorities"]


def test_no_delayed_orders_no_incident():
    s = copy.deepcopy(SNAP); s["delayed_orders"] = []
    r = run(fake_call(s))
    assert r["status"] == "completed" and r["findings"][0]["title"] == "No delayed orders"
    assert r["actions"] == [] and r["impact"] is None


def test_orders_down_partial():
    r = run(fake_call(down={"orders"}))
    assert r["status"] == "partial" and r["findings"][0]["status"] == "unknown" and r["impact"] is None


def test_inventory_down_root_cause_unknown():
    r = run(fake_call(down={"inventory"}))
    assert r["status"] == "partial"
    assert r["findings"][0]["status"] == "unknown" and "Inventory" in r["findings"][0]["title"]
    assert r["actions"] == []


def test_no_matching_sync_stays_unknown():
    s = copy.deepcopy(SNAP); s["sync_status"] = [{**x, "status": "success"} for x in s["sync_status"]]
    r = run(fake_call(s))
    assert not any(f["title"].startswith("Root cause:") for f in r["findings"])
    assert r["actions"] == []


def test_empty_tickets_ok():
    s = copy.deepcopy(SNAP); s["tickets"] = []
    r = run(fake_call(s))
    assert r["impact"]["customers_with_complaints"]["value"] == 0
    assert not any(a["action_type"] == "prioritize_tickets" for a in r["actions"])


def test_tool_failure_retried_then_gap():
    call = fake_call(broken_tools={"get_shipment_status"})
    r = run(call)
    assert sum(t == "get_shipment_status" for _, t, _ in call.calls) == 2  # 1 retry, bounded
    assert r["status"] == "partial" and any("get_shipment_status" in g for g in r["gaps"])


def test_call_budget_prevents_loops():
    r = run(fake_call(), max_calls=6)
    assert r["status"] == "partial" and len(r["trace"]) <= 6


def test_transfer_never_exceeds_stock():
    s = copy.deepcopy(SNAP)
    for w in s["product_stock_SKU-104"]["warehouses"]:
        if w["warehouse_id"] == "W2":
            w["available_quantity"] = 25  # only 5 spare above threshold 20
    r = run(fake_call(s))
    t = next(a for a in r["actions"] if a["action_type"] == "inventory_transfer")
    assert t["inputs"]["units"] == 5 and r["transfer"]["units_allocated"] <= 5


def test_truncated_list_flagged():
    s = copy.deepcopy(SNAP)
    call = fake_call(s)

    async def truncating(server, tool, args):
        d = await call(server, tool, args)
        if tool == "get_support_tickets":
            d = {**d, "total": d["total"] + 5}
        return d
    r = run(truncating)
    assert r["status"] == "partial" and any("truncated" in g for g in r["gaps"])
