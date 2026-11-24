import json
import time
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

import main
from tests.fake_mcp import SNAP, fake_call, page


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)  # template narrative, no network
    main.INVESTIGATIONS.clear()

    def caller(**kw):
        call = fake_call(**kw)

        async def wrapped(server, tool, args):
            match tool:
                case "get_order_health": return {"delayed_orders": 30}
                case "get_stock_health": return {"failed_syncs": 1}
                case "get_low_stock_products": return page([])
            return await call(server, tool, args)

        @asynccontextmanager
        async def cm():
            yield wrapped
        return cm

    monkeypatch.setattr(main, "open_caller", caller())
    with TestClient(main.app) as c:
        c.caller = caller
        yield c


def wait_done(c, inv_id, timeout=10):
    t = time.time()
    while time.time() - t < timeout:
        inv = c.get(f"/api/investigations/{inv_id}").json()
        if inv["completed_at"] or inv["status"] == "failed":
            return inv
        time.sleep(0.05)
    raise AssertionError("investigation did not finish")


def test_investigation_lifecycle(client):
    r = client.post("/api/investigations", json={})
    assert r.status_code == 201 and r.json()["status"] == "queued"
    inv = wait_done(client, r.json()["id"])
    assert inv["status"] == "awaiting_approval"
    assert inv["report"]["impact"]["recoverable_orders"]["value"] == 20
    assert inv["report"]["narrative"]["source"] == "template"
    types = [e["type"] for e in inv["events"]]
    assert types[0] == "status" and "tool_call" in types and "evidence" in types and types[-1] == "done"
    listed = client.get("/api/investigations").json()
    assert listed[0]["id"] == inv["id"] and listed[0]["pending_actions"] == 4


def test_sse_replays_and_ends(client):
    inv_id = client.post("/api/investigations", json={}).json()["id"]
    wait_done(client, inv_id)
    with client.stream("GET", f"/api/investigations/{inv_id}/events") as s:
        events = [json.loads(line[6:]) for line in s.iter_lines() if line.startswith("data: ")]
    assert events[-1]["type"] == "done"


def test_partial_when_inventory_down(client, monkeypatch):
    monkeypatch.setattr(main, "open_caller", client.caller(down={"inventory"}))
    inv = wait_done(client, client.post("/api/investigations", json={}).json()["id"])
    assert inv["status"] == "partial" and inv["report"]["gaps"]


def test_crash_marks_failed(client, monkeypatch):
    @asynccontextmanager
    async def boom():
        raise RuntimeError("runner crashed")
        yield
    monkeypatch.setattr(main, "open_caller", boom)
    inv = wait_done(client, client.post("/api/investigations", json={}).json()["id"])
    assert inv["status"] == "failed" and inv["report"] is None


def test_404(client):
    assert client.get("/api/investigations/INV-NOPE").status_code == 404


def test_overview(client):
    o = client.get("/api/overview").json()
    assert o["orders"]["delayed_orders"] == 30 and o["sync"] and o["errors"] == []
