"""Automated demo rehearsal against the running stack (stdlib only).

    python scripts/rehearse.py [runs]

Each run starts a real investigation (both Synapse MCP servers) and checks every demo number against
docs/DEMO_STATE.md. Run 1 also approves the transfer, checks the duplicate is blocked and the audit trail.
Start from a fresh backend (`scripts/start-demo.ps1 -Reset`) so the simulated ledger is empty.
"""
import json
import sys
import time
import urllib.error
import urllib.request

API = "http://127.0.0.1:8000/api"
EXPECTED = {"delayed_orders_all_causes": 30, "incident_orders": 28, "sla_breached_orders": 12, "at_risk_orders": 16,
            "affected_customers": 24, "vip_customers_affected": 4, "customers_with_complaints": 9,
            "order_value_affected": 7224.0, "units_affected": 56, "transferable_units": 40,
            "recoverable_orders": 20, "unrecoverable_orders": 8}


def req(method, path, body=None):
    r = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def check(ok, msg, fails):
    print(("  PASS " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def run(n, fails):
    t0 = time.time()
    _, inv = req("POST", "/investigations", {})
    while True:
        _, d = req("GET", f"/investigations/{inv['id']}")
        if d["report"] or d["status"] == "failed":
            break
        time.sleep(0.3)
    r = d["report"]
    print(f"run {n}: {inv['id']} status={d['status']} report in {time.time() - t0:.1f}s, "
          f"{len(r['trace']) if r else 0} MCP calls")
    check(d["status"] == "awaiting_approval" and not r["gaps"], f"status awaiting_approval, no gaps ({d['status']}, {r and r['gaps']})", fails)
    got = {k: r["impact"][k]["value"] for k in EXPECTED}
    check(got == EXPECTED, "impact numbers match DEMO_STATE" + ("" if got == EXPECTED else f": {got}"), fails)
    root = r["findings"][0]
    check(root["status"] == "likely" and "W1-WMS" in root["title"] and "SKU-104" in root["title"], f"root cause: {root['title']} ({root['status']})", fails)
    systems = {e["source_system"] for e in r["evidence"] if e["evidence_id"] in root["evidence_ids"]}
    check(systems == {"orders", "inventory"}, "root cause cites evidence from both systems", fails)
    check({t["server"] for t in r["trace"]} == {"orders", "inventory"} and all(t["ok"] for t in r["trace"]), "all MCP calls ok on both servers", fails)
    if n == 1:
        a = next(x for x in r["actions"] if x["action_type"] == "inventory_transfer")
        s, body = req("POST", f"/investigations/{inv['id']}/actions/{a['action_id']}/approve", {"approver": "rehearsal"})
        check(s == 200 and body["execution"]["status"] == "succeeded", f"transfer approved + executed ({s}, {body.get('execution', body)})", fails)
        s, _ = req("POST", f"/investigations/{inv['id']}/actions/{a['action_id']}/approve", {"approver": "rehearsal"})
        check(s == 409, f"duplicate approval blocked ({s})", fails)
        _, sim = req("GET", "/simulation")
        check(len(sim["transfers"]) == 1 and sim["transfers"][0]["units"] == 40, "exactly one simulated transfer of 40", fails)
        _, log = req("GET", f"/audit?investigation_id={inv['id']}")
        ev = {e["event"] for e in log}
        check({"investigation_started", "report_ready", "approved", "executed", "duplicate_blocked"} <= ev, "audit trail complete", fails)
        _, systems_info = req("GET", "/systems")
        counts = {s["name"]: s["mcp"]["tool_count"] for s in systems_info}
        check(counts == {"orders": 9, "inventory": 8}, f"MCP tool counts before live discovery {counts}", fails)


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    fails: list[str] = []
    for n in range(1, runs + 1):
        run(n, fails)
    print(f"\n{runs} runs, {len(fails)} failed checks")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
