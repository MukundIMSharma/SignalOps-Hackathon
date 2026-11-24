"""API tests. Seed-count asserts mirror docs/DEMO_STATE.md rows; update both together."""


def get(client, path, **params):
    r = client.get(path, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    assert get(client, "/health")["status"] == "ok"


def test_openapi_operation_ids(client):
    paths = client.get("/openapi.json").json()["paths"]
    ops = {op["operationId"] for p in paths.values() for op in p.values()}
    assert {"get_product_stock", "get_low_stock_products", "get_warehouse_inventory", "get_warehouse_status",
            "get_inventory_sync_status", "get_stock_health", "list_products", "get_product_details"} <= ops
    assert "/inventory/incidents" not in paths  # reserved for the live Synapse discovery demo


def test_products(client):
    assert get(client, "/products")["total"] == 8
    assert get(client, "/products", category="audio")["total"] == 2
    assert get(client, "/products/SKU-104")["name"] == "Aurora ANC Headphones"
    r = client.get("/products/SKU-999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_product_stock_incident(client):
    s = get(client, "/stock/SKU-104")
    by_wh = {w["warehouse_id"]: w for w in s["warehouses"]}
    assert by_wh["W1"]["available_quantity"] == 0
    assert by_wh["W1"]["last_updated"] == "2026-11-23T09:41:00"
    assert by_wh["W2"]["available_quantity"] == 60
    assert s["reorder_threshold"] == 20
    assert by_wh["W2"]["available_quantity"] - s["reorder_threshold"] == 40  # transferable (DEMO_STATE #15)
    assert client.get("/stock/SKU-999").status_code == 404


def test_stock_filter(client):
    assert get(client, "/stock")["total"] == 16
    assert get(client, "/stock", warehouse_id="W2")["total"] == 8
    assert get(client, "/stock", product_id="SKU-104", warehouse_id="W1")["items"][0]["available_quantity"] == 0


def test_low_stock(client):
    items = get(client, "/stock/low")["items"]
    assert {(i["product_id"], i["warehouse_id"]) for i in items} == {("SKU-104", "W1"), ("SKU-107", "W2")}
    assert get(client, "/stock/low", warehouse_id="W1")["total"] == 1


def test_warehouses(client):
    status = {w["warehouse_id"]: w["status"] for w in get(client, "/warehouses")["items"]}
    assert status == {"W1": "degraded", "W2": "operational"}


def test_sync_status(client):
    failed = get(client, "/sync/status", status="failed")["items"]
    assert len(failed) == 1
    f = failed[0]
    assert f["warehouse_id"] == "W1" and f["affected_products"] == ["SKU-104"]
    assert f["failing_since"] == "2026-11-23T09:42:00" and f["severity"] == "critical"
    assert get(client, "/sync/status", warehouse_id="W2")["items"][0]["status"] == "success"


def test_stock_health(client):
    h = get(client, "/analytics/stock-health")
    assert h["low_stock_positions"] == 2
    assert h["out_of_stock_positions"] == 1
    assert h["failed_syncs"] == 1
    assert h["products_affected_by_sync_failures"] == ["SKU-104"]
