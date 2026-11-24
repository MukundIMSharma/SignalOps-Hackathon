"""Transparent customer/order priority score. Weights are a documented prototype policy, not objective truth."""

WEIGHTS = {
    "vip": 30,               # customer tier = vip
    "sla_breached": 25,      # dispatch date already passed
    "per_day_overdue": 5,    # per day overdue, capped at 3 days
    "open_complaint": 20,    # open delivery_delay ticket from this customer
    "at_risk": 10,           # not breached yet, dispatch date still ahead
}
MAX_DAYS = 3


def rank_orders(orders: list[dict], customers: dict[str, dict], tickets: list[dict]) -> list[dict]:
    """Score each order; return [{order_id, customer_id, score, reasons[], order}] sorted best-first.

    Ties break on earlier expected_dispatch_date, then order_id, so ranking is fully deterministic.
    Order value is deliberately not scored (no business policy says low-value customers matter less).
    """
    complainers = {t["customer_id"] for t in tickets if t["category"] == "delivery_delay" and t["status"] == "open"}
    ranked = []
    for o in orders:
        score, reasons = 0, []
        if customers[o["customer_id"]]["tier"] == "vip":
            score += WEIGHTS["vip"]; reasons.append("VIP customer")
        if o["sla_breached"]:
            days = min(o["days_overdue"], MAX_DAYS)
            score += WEIGHTS["sla_breached"] + WEIGHTS["per_day_overdue"] * days
            reasons.append(f"SLA breached ({o['days_overdue']}d overdue)")
        else:
            score += WEIGHTS["at_risk"]; reasons.append("At risk of SLA breach")
        if o["customer_id"] in complainers:
            score += WEIGHTS["open_complaint"]; reasons.append("Open delay complaint")
        ranked.append({"order_id": o["order_id"], "customer_id": o["customer_id"], "score": score,
                       "reasons": reasons, "order": o})
    ranked.sort(key=lambda r: (-r["score"], r["order"]["expected_dispatch_date"], r["order_id"]))
    return ranked
