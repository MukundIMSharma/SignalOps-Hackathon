"""Approve / reject proposed actions and run them against a SIMULATED ledger (plan §12).

Nothing is written to the business systems: MCP tools stay read-only. Before executing, each action is
re-validated against live data read through MCP, so a stale plan can't over-commit stock.
"""
import uuid
from datetime import datetime, timezone

from agent.impact import transferable_units
from agent.orchestrator import ToolError

from . import audit

# shortcut: simulated ledger lives in memory (lost on restart); the audit log on disk keeps the history
SIM: dict = {"transfers": [], "ticket_priorities": {}, "incidents": [], "drafts": []}
NEEDS_MCP = {"inventory_transfer", "prioritize_tickets", "draft_customer_update"}  # re-validated via MCP


class ActionError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(msg)
        self.status = status


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find(inv: dict, action_id: str) -> dict:
    if not inv["report"]:
        raise ActionError(409, "Investigation has no report yet")
    a = next((a for a in inv["report"]["actions"] if a["action_id"] == action_id), None)
    if not a:
        raise ActionError(404, f"Action {action_id} not found in {inv['id']}")
    return a


async def decide(inv: dict, action_id: str, approve: bool, approver: str, note: str, call) -> dict:
    """Approve (validate + execute) or reject one action. Returns the updated action."""
    # Status flips before the first await, so a concurrent second click sees it and is blocked.
    a = find(inv, action_id)
    key = f"{inv['id']}:{action_id}"
    base = dict(investigation_id=inv["id"], action_id=action_id, action_type=a["action_type"],
                approver=approver, note=note, idempotency_key=key, inputs=a["inputs"])
    if not a["requires_approval"]:
        raise ActionError(409, f"{action_id} does not need approval")
    if a["approval_status"] != "pending":  # idempotency: one decision per action key, ever
        audit.record("duplicate_blocked", **base, current_status=a["approval_status"])
        raise ActionError(409, f"{action_id} already {a['approval_status']}; not executed again")

    a.update(approver=approver, decided_at=now(), decision_note=note, idempotency_key=key)
    if not approve:
        a["approval_status"] = "rejected"
        audit.record("rejected", **base)  # rejection changes nothing else
    else:
        a["approval_status"] = "approved"
        audit.record("approved", **base)
        try:
            result = await _execute(a, call)
            a["execution"] = {"status": "succeeded", "result": result, "error": None, "executed_at": now()}
            audit.record("executed", **base, result=result)
        except (ActionError, ToolError) as e:  # never mark a failed execution as successful
            a["execution"] = {"status": "failed", "result": None, "error": str(e), "executed_at": now()}
            audit.record("execution_failed", **base, error=str(e))
    _settle(inv)
    return a


def _settle(inv: dict):
    """Investigation leaves awaiting_approval once no approval-required action is pending."""
    r = inv["report"]
    if inv["status"] == "awaiting_approval" and not any(a["approval_status"] == "pending" for a in r["actions"]):
        inv["status"] = r["status"] = "completed"
        audit.record("investigation_completed", investigation_id=inv["id"])


async def _execute(a: dict, call) -> dict:
    inp = a["inputs"]
    match a["action_type"]:
        case "inventory_transfer":
            pid, src, dst, units = inp["product_id"], inp["source"], inp["destination"], int(inp["units"])
            if units <= 0:
                raise ActionError(422, "Transfer quantity must be positive")
            stock = await call("inventory", "get_product_stock", {"product_id": pid})  # validates product id
            whs = {w["warehouse_id"]: w for w in stock["warehouses"]}
            if src not in whs or dst not in whs or src == dst:
                raise ActionError(422, f"Invalid warehouses {src} -> {dst} for {pid}")
            already = sum(t["units"] for t in SIM["transfers"] if t["product_id"] == pid and t["source"] == src)
            spare = transferable_units(whs[src], stock["reorder_threshold"]) - already
            if units > spare:
                raise ActionError(422, f"Requested {units} units exceeds {spare} transferable from {src} "
                                       f"(available {whs[src]['available_quantity']}, threshold "
                                       f"{stock['reorder_threshold']}, already transferred {already})")
            t = {"transfer_id": f"TRF-{uuid.uuid4().hex[:6].upper()}", "product_id": pid, "source": src,
                 "destination": dst, "units": units, "at": now(), "simulated": True}
            SIM["transfers"].append(t)
            return {**t, "source_remaining_after": whs[src]["available_quantity"] - already - units}
        case "prioritize_tickets":
            tickets = {t["ticket_id"] for t in (await call("orders", "get_support_tickets", {}))["items"]}
            missing = sorted(set(inp["ticket_ids"]) - tickets)
            if missing:
                raise ActionError(422, f"Unknown ticket ids: {', '.join(missing)}")
            for tid in inp["ticket_ids"]:
                SIM["ticket_priorities"][tid] = inp["priority"]
            return {"tickets_updated": inp["ticket_ids"], "priority": inp["priority"], "simulated": True}
        case "draft_customer_update":
            names = []
            for cid in inp["customer_ids"]:  # validates every id; unknown -> ToolError -> failed
                names.append((await call("orders", "get_customer_details", {"customer_id": cid}))["name"])
            d = {"draft_id": f"DRF-{uuid.uuid4().hex[:6].upper()}", "recipients": len(names), "sent": False,
                 "subject": "Update on your NovaCommerce order",
                 "body": "Your order is delayed because of an inventory system issue at one of our warehouses. "
                         "We are moving stock to fulfil it and will confirm a dispatch date shortly.",
                 "customer_ids": inp["customer_ids"], "at": now()}
            SIM["drafts"].append(d)
            return {"draft_id": d["draft_id"], "recipients": d["recipients"], "sent": False,
                    "note": "Draft only - never sent externally"}
        case "create_internal_incident":
            inc = {"incident_id": f"SIM-INC-{len(SIM['incidents']) + 1:03d}", "title": inp["title"],
                   "severity": inp["severity"], "owner": "inventory-operations", "at": now(), "simulated": True}
            SIM["incidents"].append(inc)
            return inc
    raise ActionError(422, f"No executor for {a['action_type']}")
