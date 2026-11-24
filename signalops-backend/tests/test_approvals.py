"""Action safety tests (plan §17): rejection, approval, stock limits, ID validation, duplicates, failures, audit."""
import time
from contextlib import asynccontextmanager

import anyio
import pytest
from fastapi.testclient import TestClient

import main
from services import approvals, audit
from tests.fake_mcp import fake_call


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(audit, "PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(approvals, "SIM", {"transfers": [], "ticket_priorities": {}, "incidents": [], "drafts": []})
    main.INVESTIGATIONS.clear()

    @asynccontextmanager
    async def cm():  # like the real open_caller: exceptions leave through an anyio task group
        async with anyio.create_task_group():
            yield fake_call()
    monkeypatch.setattr(main, "open_caller", cm)
    with TestClient(main.app) as c:
        yield c


def new_inv(c):
    inv_id = c.post("/api/investigations", json={}).json()["id"]
    for _ in range(200):
        inv = c.get(f"/api/investigations/{inv_id}").json()
        if inv["completed_at"]:
            return inv
        time.sleep(0.05)
    raise AssertionError("not finished")


def act(inv, kind):
    return next(a for a in inv["report"]["actions"] if a["action_type"] == kind)


def events():
    return [e["event"] for e in audit.entries()]


def test_reject_changes_nothing(client):
    inv = new_inv(client)
    a = act(inv, "inventory_transfer")
    r = client.post(f"/api/investigations/{inv['id']}/actions/{a['action_id']}/reject", json={"approver": "ops-lead"})
    assert r.status_code == 200 and r.json()["approval_status"] == "rejected" and "execution" not in r.json()
    assert approvals.SIM["transfers"] == []
    assert "rejected" in events()


def test_approve_executes_only_that_action(client):
    inv = new_inv(client)
    a = act(inv, "inventory_transfer")
    r = client.post(f"/api/investigations/{inv['id']}/actions/{a['action_id']}/approve", json={"approver": "ops-lead"})
    body = r.json()
    assert body["approval_status"] == "approved" and body["execution"]["status"] == "succeeded"
    assert len(approvals.SIM["transfers"]) == 1 and approvals.SIM["transfers"][0]["units"] == 40
    assert approvals.SIM["ticket_priorities"] == {} and approvals.SIM["incidents"] == []
    others = client.get(f"/api/investigations/{inv['id']}").json()["report"]["actions"]
    assert sum(x["approval_status"] == "pending" for x in others) == 3
    assert events()[:2] == ["executed", "approved"]  # newest first


def test_duplicate_blocked(client):
    inv = new_inv(client)
    url = f"/api/investigations/{inv['id']}/actions/{act(inv, 'inventory_transfer')['action_id']}/approve"
    assert client.post(url, json={}).status_code == 200
    r = client.post(url, json={})
    assert r.status_code == 409 and len(approvals.SIM["transfers"]) == 1
    assert "duplicate_blocked" in events()


def test_quantity_cannot_exceed_stock_across_investigations(client):
    a1, a2 = new_inv(client), new_inv(client)  # both plan 40 units from W2's 40 spare
    client.post(f"/api/investigations/{a1['id']}/actions/{act(a1, 'inventory_transfer')['action_id']}/approve", json={})
    r = client.post(f"/api/investigations/{a2['id']}/actions/{act(a2, 'inventory_transfer')['action_id']}/approve", json={})
    ex = r.json()["execution"]
    assert ex["status"] == "failed" and "exceeds 0 transferable" in ex["error"]  # not marked successful
    assert len(approvals.SIM["transfers"]) == 1
    assert "execution_failed" in events()


def test_ids_validated(client):
    inv = new_inv(client)
    a = act(main.INVESTIGATIONS[inv["id"]], "prioritize_tickets")
    a["inputs"]["ticket_ids"] = a["inputs"]["ticket_ids"] + ["T-9999"]
    r = client.post(f"/api/investigations/{inv['id']}/actions/{a['action_id']}/approve", json={})
    assert r.json()["execution"]["status"] == "failed" and "T-9999" in r.json()["execution"]["error"]
    assert approvals.SIM["ticket_priorities"] == {}

    d = act(main.INVESTIGATIONS[inv["id"]], "draft_customer_update")
    d["inputs"]["customer_ids"] = ["C-9999"]
    r = client.post(f"/api/investigations/{inv['id']}/actions/{d['action_id']}/approve", json={})
    assert r.json()["execution"]["status"] == "failed" and approvals.SIM["drafts"] == []


def test_draft_never_sent_and_all_decided_completes(client):
    inv = new_inv(client)
    assert inv["status"] == "awaiting_approval"
    for a in inv["report"]["actions"]:
        if a["requires_approval"]:
            client.post(f"/api/investigations/{inv['id']}/actions/{a['action_id']}/approve", json={"approver": "ops-lead"})
    after = client.get(f"/api/investigations/{inv['id']}").json()
    assert after["status"] == "completed"
    assert approvals.SIM["drafts"][0]["sent"] is False
    assert "investigation_completed" in events()


def test_not_required_and_unknown(client):
    inv = new_inv(client)
    mon = act(inv, "monitor_orders")
    assert client.post(f"/api/investigations/{inv['id']}/actions/{mon['action_id']}/approve", json={}).status_code == 409
    assert client.post(f"/api/investigations/{inv['id']}/actions/A-999/approve", json={}).status_code == 404
    assert client.post(f"/api/investigations/{inv['id']}/actions/A-001/approve", json={"approver": " "}).status_code == 422


def test_approvals_and_audit_endpoints(client):
    inv = new_inv(client)
    rows = client.get("/api/approvals").json()
    assert len(rows) == 4 and all(r["approval_status"] == "pending" for r in rows) and rows[0]["evidence"]
    log = client.get(f"/api/audit?investigation_id={inv['id']}").json()
    assert {"investigation_started", "report_ready"} <= {e["event"] for e in log}
