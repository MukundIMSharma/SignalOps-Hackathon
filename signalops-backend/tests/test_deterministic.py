"""Deterministic agent logic against a snapshot of the seeded APIs (tests/fixtures/seed_snapshot.json)."""
import json
import pathlib

from agent.correlation import dispatch_after_failure, link_delays_to_sync_failures
from agent.impact import allocate_transfer, compute_impact, transferable_units
from agent.prioritization import rank_orders

S = json.loads((pathlib.Path(__file__).parent / "fixtures" / "seed_snapshot.json").read_text())
STOCK = {w["warehouse_id"]: w for w in S["product_stock_SKU-104"]["warehouses"]}


def incident():
    c = link_delays_to_sync_failures(S["delayed_orders"], S["sync_status"])
    return c, c["linked"]["SYNC-W1-WMS"]


def test_correlation_separates_unrelated_delays():
    c, linked = incident()
    assert len(linked) == 28
    assert {o["delay_reason"] for o in c["unlinked"]} == {"carrier_exception"} and len(c["unlinked"]) == 2
    assert dispatch_after_failure(linked, c["failed_syncs"][0]["failing_since"])


def test_no_failed_sync_links_nothing():
    healthy = [{**s, "status": "success"} for s in S["sync_status"]]
    c = link_delays_to_sync_failures(S["delayed_orders"], healthy)
    assert c["linked"] == {} and len(c["unlinked"]) == 30


def test_ranking_deterministic_and_explained():
    _, linked = incident()
    a = rank_orders(linked, S["customers"], S["tickets"])
    b = rank_orders(list(reversed(linked)), S["customers"], S["tickets"])
    assert [r["order_id"] for r in a] == [r["order_id"] for r in b]
    top = a[0]
    assert "VIP customer" in top["reasons"] and top["score"] >= a[-1]["score"]
    assert all(r["reasons"] for r in a)


def test_allocation_respects_stock():
    _, linked = incident()
    ranked = rank_orders(linked, S["customers"], S["tickets"])
    units = transferable_units(STOCK["W2"], S["product_stock_SKU-104"]["reorder_threshold"])
    assert units == 40
    t = allocate_transfer(ranked, units)
    qty = {o["order_id"]: o["quantity"] for o in linked}
    assert sum(qty[i] for i in t["recovered_order_ids"]) == t["units_allocated"] <= 40
    assert len(t["recovered_order_ids"]) + len(t["unrecovered_order_ids"]) == 28
    assert allocate_transfer(ranked, 0)["recovered_order_ids"] == []


def test_impact_matches_demo_state():
    c, linked = incident()
    ranked = rank_orders(linked, S["customers"], S["tickets"])
    t = allocate_transfer(ranked, 40)
    m = {k: v["value"] for k, v in compute_impact(S["delayed_orders"], linked, S["customers"], S["tickets"],
                                                   STOCK["W1"]["available_quantity"], t, 40).items()}
    assert m["delayed_orders_all_causes"] == 30 and m["incident_orders"] == 28
    assert m["sla_breached_orders"] == 12 and m["at_risk_orders"] == 16
    assert m["affected_customers"] == 24 and m["vip_customers_affected"] == 4
    assert m["customers_with_complaints"] == 9
    assert m["order_value_affected"] == 7224.0 and m["units_affected"] == 56
    assert m["stock_shortage_units"] == 56 and m["transferable_units"] == 40
    assert m["recoverable_orders"] == 20 and m["unrecoverable_orders"] == 8  # DEMO_STATE #17, #18
    assert t["units_unused"] == 0
