"""Controlled investigation workflow (plan §10). Fixed stages, bounded tool calls, no LLM in the facts path.

`call(server, tool, args)` returns the tool's parsed JSON or raises ToolError. Injected so tests can
replay the seeded snapshot and simulate outages; live runs use mcp_clients.servers.open_caller().
"""
import asyncio
import time
from collections import Counter
from typing import Any, Awaitable, Callable

from .correlation import dispatch_after_failure, link_delays_to_sync_failures
from .impact import allocate_transfer, compute_impact, transferable_units
from .prioritization import WEIGHTS, rank_orders
from .schemas import Action, Evidence, Finding, ToolEvent

Call = Callable[[str, str, dict], Awaitable[Any]]
DEFAULT_REQUEST = ("Investigate all delayed orders. Identify the root cause, which customers are affected, "
                   "the business impact, and what we should do next.")
ENDPOINTS = {  # tool -> API path template, for evidence source_endpoint
    "get_delayed_orders": "/orders/delayed", "get_support_tickets": "/tickets", "get_shipment_status": "/shipments",
    "get_customer_details": "/customers/{customer_id}", "get_inventory_sync_status": "/sync/status",
    "get_product_stock": "/stock/{product_id}", "get_warehouse_status": "/warehouses",
    "get_inventory_incidents": "/inventory/incidents",
}


class ToolError(Exception):
    pass


class Investigation:
    def __init__(self, call: Call, on_event: Callable[[dict], None] | None = None,
                 max_calls: int = 60, timeout_s: float = 20, retries: int = 1):
        self.call, self.on_event = call, on_event or (lambda e: None)
        self.max_calls, self.timeout_s, self.retries = max_calls, timeout_s, retries
        self.trace: list[ToolEvent] = []
        self.evidence: list[Evidence] = []
        self.gaps: list[str] = []
        self.as_of = ""
        self.timeline: list[dict] = []  # {at, event, source_system}

    # ---- tool access -------------------------------------------------------------------------
    async def tool(self, server: str, tool: str, args: dict | None = None) -> Any:
        args = args or {}
        last = ""
        for _ in range(self.retries + 1):  # read-only tools only, so a bounded retry is safe
            if len(self.trace) >= self.max_calls:
                raise ToolError(f"tool-call budget of {self.max_calls} exhausted")
            t0 = time.perf_counter()
            try:
                data = await asyncio.wait_for(self.call(server, tool, args), self.timeout_s)
                ok, summary = True, _summarize(data)
            except (ToolError, asyncio.TimeoutError, OSError) as e:
                data, ok, summary = None, False, f"{type(e).__name__}: {e}"[:200]
            self._emit(ToolEvent(seq=len(self.trace) + 1, server=server, tool=tool, args=args, ok=ok,
                                 ms=int((time.perf_counter() - t0) * 1000), summary=summary))
            if ok:
                if isinstance(data, dict) and data.get("as_of"):
                    self.as_of = data["as_of"]
                return data
            last = summary
        raise ToolError(f"{server}.{tool} failed: {last}")

    async def items(self, server: str, tool: str, args: dict | None = None) -> list[dict] | None:
        """Full list from a list tool, or None (gap recorded) if the call fails."""
        try:
            data = await self.tool(server, tool, args)
        except ToolError as e:
            self.gaps.append(str(e))
            return None
        if data["total"] != len(data["items"]):
            self.gaps.append(f"{server}.{tool} returned {len(data['items'])} of {data['total']} items (truncated)")
        return data["items"]

    def _emit(self, ev: ToolEvent):
        self.trace.append(ev)
        self.on_event({"type": "tool_call", **ev.model_dump()})

    def add_evidence(self, claim, status, system, tool, entity_ids, data, args=None) -> str:
        eid = f"E-{len(self.evidence) + 1:03d}"
        self.evidence.append(Evidence(evidence_id=eid, claim=claim, status=status, source_system=system,
                                      source_tool=tool, source_endpoint=ENDPOINTS[tool].format(**args) if args else ENDPOINTS[tool],
                                      entity_ids=entity_ids, observed_at=self.as_of, data=data))
        self.on_event({"type": "evidence", "evidence_id": eid, "claim": claim, "status": status})
        return eid

    # ---- workflow ----------------------------------------------------------------------------
    async def run(self, request: str = DEFAULT_REQUEST) -> dict:
        self.on_event({"type": "stage", "stage": "orders"})
        delayed = await self.items("orders", "get_delayed_orders")
        tickets = await self.items("orders", "get_support_tickets")
        shipments = await self.items("orders", "get_shipment_status")
        self.on_event({"type": "stage", "stage": "inventory"})
        syncs = await self.items("inventory", "get_inventory_sync_status")
        warehouses = await self.items("inventory", "get_warehouse_status")
        incidents = None
        if "get_inventory_incidents" in getattr(self.call, "tools", {}).get("inventory", set()):
            self.on_event({"type": "capability", "tool": "get_inventory_incidents", "server": "inventory"})
            incidents = await self.items("inventory", "get_inventory_incidents")

        if delayed is None:
            return self._report(request, findings=[Finding(
                finding_id="F-001", title="Investigation incomplete: Orders system unavailable", severity="high",
                status="unknown", evidence_ids=[], summary="Delayed orders could not be retrieved, so no root cause "
                "or customer impact can be determined.", confidence_explanation="No order data was available.")])
        if not delayed:
            return self._report(request, findings=[Finding(
                finding_id="F-001", title="No delayed orders", severity="info", status="confirmed", evidence_ids=[
                    self.add_evidence("No orders are currently delayed", "confirmed", "orders", "get_delayed_orders",
                                      [], {"delayed_orders": 0})],
                summary="There is no delay incident to investigate.", confidence_explanation="Orders system "
                "returned an empty delayed-order list.")])

        self.on_event({"type": "stage", "stage": "correlation"})
        reasons = Counter(o["delay_reason"] for o in delayed)
        e_delayed = self.add_evidence(
            f"{len(delayed)} orders are delayed: " + ", ".join(f"{n} {r}" for r, n in reasons.most_common()),
            "confirmed", "orders", "get_delayed_orders", sorted({o["product_id"] for o in delayed}),
            {"delayed_orders": len(delayed), "by_reason": dict(reasons),
             "by_product_warehouse": {f"{p}@{w}": n for (p, w), n in
                                      Counter((o["product_id"], o["warehouse_id"]) for o in delayed).items()}})

        corr = link_delays_to_sync_failures(delayed, syncs or [])
        findings: list[Finding] = []
        actions: list[Action] = []
        incident_orders: list[dict] = []
        impact = priorities = transfer = None

        for sync in corr["failed_syncs"]:
            linked = corr["linked"][sync["sync_id"]]
            if not linked:
                continue
            wh = sync["warehouse_id"]
            products = sorted({o["product_id"] for o in linked})
            incident_orders += linked
            e_sync = self.add_evidence(
                f"{sync['source']} sync for {', '.join(sync['affected_products'])} has been failing since "
                f"{sync['failing_since']} ({sync['error_code']})", "confirmed", "inventory",
                "get_inventory_sync_status", [sync["sync_id"], wh, *sync["affected_products"]],
                {k: sync[k] for k in ("status", "last_success", "failing_since", "error_code", "error_message",
                                      "severity")})
            breached = sorted(o["expected_dispatch_date"] for o in linked if o["sla_breached"])
            self.timeline += [
                {"at": sync["last_success"], "event": f"Last successful {sync['source']} sync", "source_system": "inventory"},
                {"at": sync["failing_since"], "event": f"{sync['source']} sync starts failing ({sync['error_code']})",
                 "source_system": "inventory"},
                {"at": min(o["expected_dispatch_date"] for o in linked),
                 "event": "First affected order due for dispatch (allocation fails)", "source_system": "orders"},
            ] + ([{"at": breached[-1], "event": f"Latest dispatch-date breach so far ({len(breached)} breached)",
                   "source_system": "orders"}] if breached else [])
            timing_ok = dispatch_after_failure(linked, sync["failing_since"])
            e_timing = self.add_evidence(
                f"All {len(linked)} linked orders were due for dispatch after the sync began failing" if timing_ok
                else "Some linked orders were due before the sync failure began", "confirmed" if timing_ok
                else "hypothesis", "orders", "get_delayed_orders", [o["order_id"] for o in linked],
                {"earliest_dispatch": min(o["expected_dispatch_date"] for o in linked),
                 "failing_since": sync["failing_since"]})
            ev = [e_delayed, e_sync, e_timing]
            stale_zero = True
            stock_by_product = {}
            for p in products:
                try:
                    st = await self.tool("inventory", "get_product_stock", {"product_id": p})
                except ToolError as e:
                    self.gaps.append(str(e)); stale_zero = False
                    continue
                stock_by_product[p] = st
                at = next((w for w in st["warehouses"] if w["warehouse_id"] == wh), None)
                zero = at is not None and at["available_quantity"] == 0
                stale = at is not None and at["last_updated"] <= sync["last_success"]
                stale_zero &= zero and stale
                ev.append(self.add_evidence(
                    f"{p} at {wh} shows {at['available_quantity'] if at else 'no'} available"
                    + (f", last updated {at['last_updated']} (before the sync failure; stale)" if stale else ""),
                    "confirmed", "inventory", "get_product_stock", [p, wh],
                    {"warehouses": {w["warehouse_id"]: w["available_quantity"] for w in st["warehouses"]},
                     "last_updated": at["last_updated"] if at else None, "reorder_threshold": st["reorder_threshold"]},
                    {"product_id": p}))
            for inc in incidents or []:
                if inc["warehouse_id"] == wh and inc["product_id"] in products:
                    ev.append(self.add_evidence(
                        f"Inventory system incident {inc['incident_id']} ({inc['severity']}): {inc['incident_type']} "
                        f"for {inc['product_id']} at {wh} since {inc['occurred_at']}", "confirmed", "inventory",
                        "get_inventory_incidents", [inc["incident_id"], inc["product_id"], wh], inc))
            wh_status = next((w["status"] for w in warehouses or [] if w["warehouse_id"] == wh), None)
            if wh_status and wh_status != "operational":
                ev.append(self.add_evidence(f"Warehouse {wh} status is {wh_status}", "confirmed", "inventory",
                                            "get_warehouse_status", [wh], {"status": wh_status}))
            all_alloc = all(o["delay_reason"] == "stock_allocation_failed" for o in linked)
            status = "likely" if (timing_ok and stale_zero and all_alloc) else "hypothesis"
            findings.append(Finding(
                finding_id=f"F-{len(findings) + 1:03d}", severity="critical", status=status, evidence_ids=ev,
                title=f"Root cause: {sync['source']} sync failure left {', '.join(products)} availability at {wh} stale",
                summary=f"Since {sync['failing_since']} the {sync['source']} stock sync has been rejected "
                        f"({sync['error_code']}). {', '.join(products)} at {wh} reads 0 available, so "
                        f"{len(linked)} orders failed stock allocation and are delayed.",
                confidence_explanation="Each fact is confirmed in its source system (failed sync, zero/stale stock, "
                "orders' delay reason, dispatch timing). The causal link is inferred from matching SKU, warehouse "
                "and timing, so it is 'likely', not 'confirmed'. Actual physical stock at the warehouse is unknown "
                "because availability is stale." if status == "likely" else "Some supporting checks failed or were "
                "unavailable; treat as unverified."))

        # unrelated delays
        if corr["unlinked"]:
            unlinked_ids = {o["order_id"] for o in corr["unlinked"]}
            exc = [s for s in shipments or [] if s["order_id"] in unlinked_ids and s["status"] == "exception"]
            ev = [e_delayed]
            if exc:
                ev.append(self.add_evidence(f"{len(exc)} other delayed orders have carrier exception shipments",
                                            "confirmed", "orders", "get_shipment_status",
                                            [s["order_id"] for s in exc],
                                            {s["order_id"]: s["tracking_status"] for s in exc}))
            all_carrier = len(exc) == len(unlinked_ids)
            findings.append(Finding(
                finding_id=f"F-{len(findings) + 1:03d}", severity="low",
                status="confirmed" if all_carrier else ("unknown" if not corr["failed_syncs"] else "hypothesis"),
                evidence_ids=ev, title=f"{len(unlinked_ids)} delayed orders not linked to an inventory failure",
                summary=(f"{len(exc)} are carrier exceptions in transit; " if exc else "")
                + "these are not part of the inventory incident.",
                confidence_explanation="Shipment status shows a carrier exception for each." if all_carrier
                else "No matching sync failure or carrier exception explains all of them."))

        if not incident_orders:
            if syncs is None:
                findings.insert(0, Finding(
                    finding_id="F-000", title="Root cause unknown: Inventory system unavailable", severity="high",
                    status="unknown", evidence_ids=[e_delayed], summary="Delayed orders exist but inventory and "
                    "sync data could not be retrieved to explain them.",
                    confidence_explanation="Inventory MCP calls failed; no inventory evidence available."))
            return self._report(request, findings=findings)

        # customers, impact, priorities
        self.on_event({"type": "stage", "stage": "impact"})
        customers = {}
        for cid in sorted({o["customer_id"] for o in incident_orders}):
            try:
                customers[cid] = await self.tool("orders", "get_customer_details", {"customer_id": cid})
            except ToolError as e:
                self.gaps.append(str(e))
        known = [o for o in incident_orders if o["customer_id"] in customers]
        tickets = tickets or []
        delay_tix = sorted(t["created_at"] for t in tickets if t["customer_id"] in customers and t["category"] == "delivery_delay")
        if delay_tix:
            self.timeline.append({"at": delay_tix[0], "event": f"First customer delay complaint ({len(delay_tix)} so far)",
                                  "source_system": "orders"})
        ranked = rank_orders(known, customers, tickets)

        transfer_plan = self._plan_transfer(incident_orders, stock_by_product, ranked)
        transfer = transfer_plan["allocation"] if transfer_plan else {"recovered_order_ids": [],
                                                                       "unrecovered_order_ids": [r["order_id"] for r in ranked],
                                                                       "units_allocated": 0, "units_unused": 0}
        units_at_wh = sum(next((w["available_quantity"] for w in s["warehouses"]
                                if w["warehouse_id"] == incident_orders[0]["warehouse_id"]), 0)
                          for s in stock_by_product.values())
        impact = compute_impact(delayed, known, customers, tickets, units_at_wh, transfer,
                                transfer_plan["units"] if transfer_plan else 0)
        complainers = {t["customer_id"] for t in tickets if t["category"] == "delivery_delay" and t["status"] == "open"}
        vip = sorted(c for c in customers if customers[c]["tier"] == "vip")
        e_cust = self.add_evidence(f"{len(vip)} affected customers are VIP", "confirmed", "orders",
                                   "get_customer_details", vip, {"vip_customers": vip}) if vip else None
        e_tix = self.add_evidence(f"{len(complainers & set(customers))} affected customers have open delay tickets",
                                  "confirmed", "orders", "get_support_tickets", sorted(complainers & set(customers)),
                                  {"ticket_ids": sorted(t["ticket_id"] for t in tickets
                                                        if t["customer_id"] in customers
                                                        and t["category"] == "delivery_delay")})
        recovered = set(transfer["recovered_order_ids"])
        priorities = [{**{k: r[k] for k in ("order_id", "customer_id", "score", "reasons")},
                       "rank": i + 1, "customer_name": customers[r["customer_id"]]["name"],
                       "tier": customers[r["customer_id"]]["tier"], "has_open_complaint": r["customer_id"] in complainers,
                       "quantity": r["order"]["quantity"], "total_amount": r["order"]["total_amount"],
                       "sla_breached": r["order"]["sla_breached"], "recoverable_by_transfer": r["order_id"] in recovered}
                      for i, r in enumerate(ranked)]
        findings.append(Finding(
            finding_id=f"F-{len(findings) + 1:03d}", severity="high", status="confirmed",
            evidence_ids=[e for e in (e_delayed, e_cust, e_tix) if e],
            title=f"{impact['affected_customers']['value']} customers affected, "
                  f"{impact['order_value_affected']['value']:,.2f} in delayed order value",
            summary=f"{impact['sla_breached_orders']['value']} orders already breached dispatch SLA and "
                    f"{impact['at_risk_orders']['value']} more are at risk. {impact['vip_customers_affected']['value']} "
                    f"VIP customers and {impact['customers_with_complaints']['value']} customers with open complaints "
                    "are affected (these groups overlap).",
            confidence_explanation="Counted directly from Orders system records.",
            impact_metrics={k: impact[k]["value"] for k in ("incident_orders", "sla_breached_orders",
                                                            "affected_customers", "order_value_affected")}))
        if transfer_plan:
            findings.append(Finding(
                finding_id=f"F-{len(findings) + 1:03d}", severity="medium", status="likely",
                evidence_ids=transfer_plan["evidence_ids"],
                title=f"Transfer from {transfer_plan['source']} can recover {len(recovered)} of {len(ranked)} orders",
                summary=f"{transfer_plan['source']} can spare {transfer_plan['units']} units while staying at its "
                        f"reorder threshold. Allocated in priority order, that covers {len(recovered)} orders; "
                        f"{len(ranked) - len(recovered)} remain blocked until the sync is fixed.",
                confidence_explanation="Projection: assumes the transfer executes and the source stock reading is "
                                       "current (its sync is healthy).",
                impact_metrics={"recoverable_orders": len(recovered),
                                "unrecoverable_orders": len(ranked) - len(recovered)}))
        actions = self._actions(findings, incident_orders, customers, complainers, tickets, transfer_plan, transfer)
        return self._report(request, findings=findings, impact=impact, priorities=priorities, transfer=transfer,
                            actions=actions, transfer_plan=transfer_plan)

    def _plan_transfer(self, incident_orders, stock_by_product, ranked) -> dict | None:
        # shortcut: single-product incidents only (the seeded scenario); multi-SKU needs per-product allocation
        if len(stock_by_product) != 1:
            return None
        (pid, st), = stock_by_product.items()
        dest = incident_orders[0]["warehouse_id"]
        sources = [(transferable_units(w, st["reorder_threshold"]), w["warehouse_id"])
                   for w in st["warehouses"] if w["warehouse_id"] != dest]
        units, src = max(sources, default=(0, None))
        if not units:
            return None
        ev = [e.evidence_id for e in self.evidence if e.source_tool == "get_product_stock" and pid in e.entity_ids]
        return {"product_id": pid, "source": src, "destination": dest, "units": units, "evidence_ids": ev,
                "allocation": allocate_transfer(ranked, units)}

    def _actions(self, findings, incident_orders, customers, complainers, tickets, plan, transfer) -> list[Action]:
        root = findings[0]
        acts = []

        def add(**kw):
            acts.append(Action(action_id=f"A-{len(acts) + 1:03d}", **kw))

        if plan:
            add(action_type="inventory_transfer", risk_level="high", requires_approval=True,
                description=f"Transfer {plan['units']} units of {plan['product_id']} from {plan['source']} to "
                            f"{plan['destination']} (simulated)",
                inputs={k: plan[k] for k in ("product_id", "source", "destination", "units")},
                affected_entities=[plan["product_id"], plan["source"], plan["destination"],
                                   *transfer["recovered_order_ids"]],
                evidence_ids=plan["evidence_ids"],
                expected_outcome=f"{len(transfer['recovered_order_ids'])} delayed orders can be allocated and dispatched")
        open_tix = sorted(t["ticket_id"] for t in tickets if t["customer_id"] in customers
                          and t["category"] == "delivery_delay" and t["status"] == "open")
        if open_tix:
            add(action_type="prioritize_tickets", risk_level="medium", requires_approval=True,
                description=f"Raise priority of {len(open_tix)} open delay tickets (simulated)",
                inputs={"ticket_ids": open_tix, "priority": "high"}, affected_entities=open_tix,
                evidence_ids=root.evidence_ids[:1],
                expected_outcome="Support handles complaining affected customers first")
        add(action_type="draft_customer_update", risk_level="low", requires_approval=True,
            description=f"Draft delay notice for {len(customers)} affected customers (draft only, never sent)",
            inputs={"customer_ids": sorted(customers)}, affected_entities=sorted(customers),
            evidence_ids=root.evidence_ids[:1], expected_outcome="Draft ready for human review")
        add(action_type="create_internal_incident", risk_level="low", requires_approval=True,
            description="Open internal incident for inventory operations to fix the failing sync (simulated)",
            inputs={"title": root.title, "severity": root.severity}, affected_entities=root.evidence_ids,
            evidence_ids=root.evidence_ids, expected_outcome="Inventory ops owns the sync fix")
        if transfer["unrecovered_order_ids"]:
            add(action_type="monitor_orders", risk_level="low", requires_approval=False, approval_status="not_required",
                description=f"Monitor {len(transfer['unrecovered_order_ids'])} orders not covered by the transfer",
                inputs={"order_ids": transfer["unrecovered_order_ids"]},
                affected_entities=transfer["unrecovered_order_ids"], evidence_ids=root.evidence_ids[:1],
                expected_outcome="Dispatch once sync is restored")
        return acts

    def _report(self, request, findings, impact=None, priorities=None, transfer=None, actions=None,
                transfer_plan=None) -> dict:
        actions = actions or []
        status = ("partial" if self.gaps else
                  "awaiting_approval" if any(a.requires_approval for a in actions) else "completed")
        self.on_event({"type": "stage", "stage": "done", "status": status})
        return {
            "request": request, "status": status, "as_of": self.as_of,
            "findings": [f.model_dump() for f in findings],
            "evidence": [e.model_dump() for e in self.evidence],
            "impact": impact, "priorities": priorities, "transfer": transfer,
            "transfer_plan": {k: v for k, v in transfer_plan.items() if k != "allocation"} if transfer_plan else None,
            "actions": [a.model_dump() for a in actions],
            "gaps": self.gaps,
            "trace": [t.model_dump() for t in self.trace],
            "prioritization_weights": WEIGHTS,
            "timeline": sorted(self.timeline + ([{"at": self.as_of, "event": "Investigation data snapshot (as_of)",
                                                  "source_system": "signalops"}] if self.as_of else []),
                               key=lambda e: e["at"]),
        }


def _summarize(data: Any) -> str:
    if isinstance(data, dict) and "items" in data:
        return f"{len(data['items'])} items"
    if isinstance(data, dict):
        return ", ".join(f"{k}={v}" for k, v in list(data.items())[:3])[:200]
    return str(data)[:200]
