"""SignalOps backend: investigations (+SSE), overview and systems pages. Business data only via Synapse MCP.

Run: .venv/Scripts/python -m uvicorn main:app --port 8000
"""
import asyncio
import json
import pathlib
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.narrative import narrate
from agent.orchestrator import DEFAULT_REQUEST, Investigation, ToolError
from mcp_clients.servers import SERVERS, connect, open_caller
from services import approvals, audit

ROOT = pathlib.Path(__file__).resolve().parent.parent
app = FastAPI(title="SignalOps API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# shortcut: in-memory store, lost on restart; persist to SQLite if history must survive restarts
INVESTIGATIONS: dict[str, dict] = {}
KNOWN_TOOLS: dict[str, set[str]] = {}  # first tool list seen per server; later additions are flagged "new"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class StartRequest(BaseModel):
    request: str = DEFAULT_REQUEST


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "signalops-backend"}


# ---- investigations ----------------------------------------------------------------------------
@app.post("/api/investigations", status_code=201)
async def start_investigation(body: StartRequest):
    inv_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    inv = {"id": inv_id, "request": body.request, "status": "queued", "created_at": now(),
           "completed_at": None, "events": [], "report": None}
    INVESTIGATIONS[inv_id] = inv
    audit.record("investigation_started", investigation_id=inv_id, request=body.request)
    asyncio.create_task(_run(inv))
    return _public(inv)


async def _run(inv: dict):
    def emit(e: dict):
        inv["events"].append({**e, "at": now()})

    inv["status"] = "investigating"
    emit({"type": "status", "status": "investigating"})
    try:
        async with open_caller() as call:
            report = await Investigation(call, on_event=emit).run(inv["request"])
    except Exception as e:  # unexpected crash: fail loudly, never a fake result
        inv["status"] = "failed"
        audit.record("investigation_failed", investigation_id=inv["id"], error=f"{type(e).__name__}: {e}"[:300])
        emit({"type": "status", "status": "failed", "error": f"{type(e).__name__}: {e}"[:300]})
        return
    report["narrative"] = {"text": None, "source": "pending", "model": None, "error": None}
    inv["report"], inv["status"] = report, report["status"]
    audit.record("report_ready", investigation_id=inv["id"], status=report["status"],
                 root_cause=report["findings"][0]["title"] if report["findings"] else None,
                 proposed_actions=[a["action_id"] for a in report["actions"]], gaps=report["gaps"])
    emit({"type": "report", "status": report["status"]})
    report["narrative"] = await narrate(report)  # report is already visible; summary arrives later
    emit({"type": "narrative", "source": report["narrative"]["source"]})
    inv["completed_at"] = now()
    emit({"type": "done", "status": inv["status"]})


def _public(inv: dict, full: bool = False) -> dict:
    out = {k: inv[k] for k in ("id", "request", "status", "created_at", "completed_at")}
    r = inv["report"]
    if r:
        out["headline"] = r["findings"][0]["title"] if r["findings"] else None
        out["pending_actions"] = sum(a["approval_status"] == "pending" for a in r["actions"])
    if full:
        out["report"] = r
        out["events"] = inv["events"]
    return out


@app.get("/api/investigations")
def list_investigations():
    return [_public(i) for i in sorted(INVESTIGATIONS.values(), key=lambda i: i["created_at"], reverse=True)]


def _get(inv_id: str) -> dict:
    if inv_id not in INVESTIGATIONS:
        raise HTTPException(404, f"Investigation {inv_id} not found")
    return INVESTIGATIONS[inv_id]


@app.get("/api/investigations/{inv_id}")
def get_investigation(inv_id: str):
    return _public(_get(inv_id), full=True)


@app.get("/api/investigations/{inv_id}/events")
async def stream_events(inv_id: str):
    inv = _get(inv_id)

    async def gen():
        sent = 0
        while True:
            # shortcut: polls the event list every 200ms; fine for a handful of viewers
            while sent < len(inv["events"]):
                e = inv["events"][sent]; sent += 1
                yield f"data: {json.dumps(e)}\n\n"
                if e["type"] == "done" or (e["type"] == "status" and e["status"] == "failed"):
                    return
            await asyncio.sleep(0.2)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


# ---- approvals / audit / simulation -------------------------------------------------------------
class Decision(BaseModel):
    approver: str = "demo-operator"
    note: str = ""


async def _decide(inv_id: str, action_id: str, approve: bool, body: Decision):
    if not body.approver.strip():
        raise HTTPException(422, "approver is required")
    inv = _get(inv_id)
    try:
        if approve and approvals.find(inv, action_id)["action_type"] in approvals.NEEDS_MCP:
            async with open_caller() as call:
                # catch inside: the MCP task group would wrap it in an ExceptionGroup on the way out
                try:
                    return await approvals.decide(inv, action_id, True, body.approver, body.note, call)
                except approvals.ActionError as e:
                    err = e
        else:
            return await approvals.decide(inv, action_id, approve, body.approver, body.note, None)
    except approvals.ActionError as e:
        err = e
    raise HTTPException(err.status, str(err))


@app.post("/api/investigations/{inv_id}/actions/{action_id}/approve")
async def approve_action(inv_id: str, action_id: str, body: Decision = Decision()):
    return await _decide(inv_id, action_id, True, body)


@app.post("/api/investigations/{inv_id}/actions/{action_id}/reject")
async def reject_action(inv_id: str, action_id: str, body: Decision = Decision()):
    return await _decide(inv_id, action_id, False, body)


@app.get("/api/approvals")
def list_approvals():
    rows = [{**a, "investigation_id": i["id"], "investigation_status": i["status"], "created_at": i["created_at"],
             "evidence": [e for e in i["report"]["evidence"] if e["evidence_id"] in a["evidence_ids"]]}
            for i in INVESTIGATIONS.values() if i["report"] for a in i["report"]["actions"] if a["requires_approval"]]
    return sorted(rows, key=lambda r: (r["approval_status"] != "pending", r["created_at"]), reverse=False)


@app.get("/api/audit")
def audit_log(investigation_id: str | None = None):
    return audit.entries(investigation_id)


@app.get("/api/simulation")
def simulation():
    return approvals.SIM


# ---- overview ----------------------------------------------------------------------------------
@app.get("/api/overview")
async def overview():
    out = {"orders": None, "stock": None, "sync": None, "low_stock": None, "errors": [], "latest_investigation": None}
    async with open_caller() as call:
        for key, server, tool in (("orders", "orders", "get_order_health"), ("stock", "inventory", "get_stock_health"),
                                  ("sync", "inventory", "get_inventory_sync_status"),
                                  ("low_stock", "inventory", "get_low_stock_products")):
            try:
                data = await asyncio.wait_for(call(server, tool, {}), 20)
                out[key] = data["items"] if "items" in data else data
            except (ToolError, asyncio.TimeoutError) as e:
                out["errors"].append(f"{server}.{tool}: {e}")
    done = [i for i in INVESTIGATIONS.values() if i["report"]]
    if done:
        latest = max(done, key=lambda i: i["created_at"])
        out["latest_investigation"] = {**_public(latest), "impact": latest["report"]["impact"]}
    return out


# ---- systems / MCP -----------------------------------------------------------------------------
@app.get("/api/systems")
async def systems():
    return await asyncio.gather(*(_system(name, cfg) for name, cfg in SERVERS.items()))


async def _system(name: str, cfg: dict) -> dict:
    out = {"name": name, "repo": cfg["repo"], "server_id": cfg["server_id"], "base_url": cfg["base_url"],
           "api": {"healthy": False, "endpoint_count": None, "error": None},
           "mcp": {"connected": False, "tools": [], "tool_count": 0, "error": None, "connect_ms": None},
           "last_discovery": _last_discovery(cfg["repo"])}
    try:  # direct HTTP: health check only (plan §5)
        async with httpx.AsyncClient(timeout=3) as c:
            out["api"]["healthy"] = (await c.get(cfg["base_url"] + "/health")).status_code == 200
            paths = (await c.get(cfg["base_url"] + "/openapi.json")).json()["paths"]
            out["api"]["endpoint_count"] = sum(len(v) for v in paths.values())
    except Exception as e:
        out["api"]["error"] = f"{type(e).__name__}: {e}"[:200]
    t0 = time.perf_counter()
    try:
        async with connect(name) as s:
            tools = (await asyncio.wait_for(s.list_tools(), 15)).tools
        known = KNOWN_TOOLS.setdefault(name, {t.name for t in tools})
        out["mcp"].update(connected=True, tool_count=len(tools), connect_ms=int((time.perf_counter() - t0) * 1000),
                          tools=[{"name": t.name, "description": t.description, "new": t.name not in known,
                                  "params": list((t.input_schema or {}).get("properties", {}))} for t in tools])
    except Exception as e:
        out["mcp"]["error"] = f"{type(e).__name__}: {e}"[:200]
    return out


def _last_discovery(repo: str) -> str | None:
    logs = list((ROOT / repo / ".synapse" / "discover").glob("*.jsonl"))
    if not logs:
        return None
    return datetime.fromtimestamp(max(p.stat().st_mtime for p in logs), timezone.utc).isoformat(timespec="seconds")
