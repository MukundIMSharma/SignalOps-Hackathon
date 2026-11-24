"""API tests. Seed-count asserts mirror docs/DEMO_STATE.md rows; update both together."""


def get(client, path, **params):
    r = client.get(path, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    assert get(client, "/health")["status"] == "ok"


def test_openapi_operation_ids(client):
    ops = {op["operationId"] for p in client.get("/openapi.json").json()["paths"].values() for op in p.values()}
    assert {"get_delayed_orders", "get_order_details", "get_customer_details", "get_customer_orders",
            "get_shipment_status", "get_order_health", "get_at_risk_orders", "get_support_tickets"} <= ops


def test_list_filter_paginate(client):
    page = get(client, "/orders", limit=10, offset=0)
    assert page["total"] == 60 and len(page["items"]) == 10
    page2 = get(client, "/orders", limit=10, offset=10)
    assert page["items"][0]["order_id"] != page2["items"][0]["order_id"]
    assert get(client, "/orders", product_id="SKU-104", warehouse_id="W1", status="delayed")["total"] == 28
    assert get(client, "/orders", priority="high", status="delayed")["total"] == 5
    assert get(client, "/orders", order_date_from="2026-11-24T00:00:00")["total"] > 0


def test_delayed_counts(client):
    delayed = get(client, "/orders/delayed")
    assert delayed["total"] == 30
    incident = get(client, "/orders/delayed", delay_reason="stock_allocation_failed")["items"]
    assert len(incident) == 28
    assert all(o["product_id"] == "SKU-104" and o["warehouse_id"] == "W1" and o["shipment_id"] is None
               for o in incident)
    assert sum(o["sla_breached"] for o in incident) == 12
    assert sum(o["quantity"] for o in incident) == 56
    assert round(sum(o["total_amount"] for o in incident), 2) == 7224.00
    assert len({o["customer_id"] for o in incident}) == 24
    carrier = get(client, "/orders/delayed", delay_reason="carrier_exception")["items"]
    assert len(carrier) == 2 and not any(o["sla_breached"] for o in carrier)


def test_incident_dispatch_dates_after_sync_failure(client):
    incident = get(client, "/orders/delayed", delay_reason="stock_allocation_failed")["items"]
    assert min(o["expected_dispatch_date"] for o in incident) > "2026-11-23T09:42:00"


def test_at_risk(client):
    items = get(client, "/orders/at-risk")["items"]
    assert len(items) == 16 and not any(o["sla_breached"] for o in items)


def test_order_detail_and_404(client):
    oid = get(client, "/orders/delayed")["items"][0]["order_id"]
    assert get(client, f"/orders/{oid}")["order_id"] == oid
    r = client.get("/orders/O-9999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_validation_error_shape(client):
    r = client.get("/orders", params={"limit": 0})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_customers(client):
    incident = get(client, "/orders/delayed", delay_reason="stock_allocation_failed")["items"]
    affected = {o["customer_id"] for o in incident}
    vips = {c for c in affected if get(client, f"/customers/{c}")["tier"] == "vip"}
    assert vips == {"C-1003", "C-1008", "C-1015", "C-1021"}
    assert get(client, "/customers/C-1003/orders")["total"] >= 2
    assert client.get("/customers/C-9999").status_code == 404
    assert client.get("/customers/C-9999/orders").status_code == 404


def test_tickets(client):
    assert get(client, "/tickets")["total"] == 11
    delay = get(client, "/tickets", category="delivery_delay", status="open")["items"]
    incident_customers = {o["customer_id"] for o in
                          get(client, "/orders/delayed", delay_reason="stock_allocation_failed")["items"]}
    assert len({t["customer_id"] for t in delay}) == 9
    assert {t["customer_id"] for t in delay} <= incident_customers


def test_shipments(client):
    exc = get(client, "/shipments", status="exception")["items"]
    assert len(exc) == 2
    oid = exc[0]["order_id"]
    assert get(client, "/shipments", order_id=oid)["total"] == 1


def test_order_health(client):
    h = get(client, "/analytics/order-health")
    assert h["total_orders"] == 60
    assert h["delayed_orders"] == 30
    assert h["delayed_by_reason"] == {"stock_allocation_failed": 28, "carrier_exception": 2}
    assert h["sla_breached_orders"] == 12
    assert h["at_risk_orders"] == 16
    assert h["open_delay_tickets"] == 9
    assert h["open_tickets"] == 10
