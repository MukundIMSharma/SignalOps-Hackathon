"""Deterministic impact metrics and transfer allocation. Every metric carries its definition."""


def transferable_units(source_stock: dict, reorder_threshold: int) -> int:
    """Units the source warehouse can give without dropping below its reorder threshold (safety stock)."""
    return max(source_stock["available_quantity"] - reorder_threshold, 0)


def allocate_transfer(ranked: list[dict], units: int) -> dict:
    """Greedy in priority order; an order that doesn't fit is skipped, later smaller ones may still fit."""
    recovered, unrecovered, left = [], [], units
    for r in ranked:
        q = r["order"]["quantity"]
        if q <= left:
            recovered.append(r["order_id"]); left -= q
        else:
            unrecovered.append(r["order_id"])
    return {"recovered_order_ids": recovered, "unrecovered_order_ids": unrecovered,
            "units_allocated": units - left, "units_unused": left}


def metric(value, definition: str) -> dict:
    return {"value": value, "definition": definition}


def compute_impact(all_delayed: list[dict], incident_orders: list[dict], customers: dict[str, dict],
                   tickets: list[dict], affected_stock_available: int, transfer: dict, transfer_units: int) -> dict:
    affected = {o["customer_id"] for o in incident_orders}
    complainers = {t["customer_id"] for t in tickets if t["category"] == "delivery_delay" and t["status"] == "open"}
    units = sum(o["quantity"] for o in incident_orders)
    return {
        "delayed_orders_all_causes": metric(len(all_delayed), "Orders with status=delayed, any cause."),
        "incident_orders": metric(len(incident_orders), "Delayed orders linked to the failed sync (subset of all delayed)."),
        "sla_breached_orders": metric(sum(o["sla_breached"] for o in incident_orders),
                                      "Incident orders past expected dispatch date (subset of incident orders)."),
        "at_risk_orders": metric(sum(not o["sla_breached"] for o in incident_orders),
                                 "Incident orders not yet past dispatch date (subset; breached + at risk = incident)."),
        "affected_customers": metric(len(affected), "Distinct customers with at least one incident order."),
        "vip_customers_affected": metric(sum(customers[c]["tier"] == "vip" for c in affected),
                                         "Affected customers with tier=vip (subset of affected customers)."),
        "customers_with_complaints": metric(len(affected & complainers),
                                            "Affected customers with an open delivery_delay ticket (subset; may overlap VIP)."),
        "order_value_affected": metric(round(sum(o["total_amount"] for o in incident_orders), 2),
                                       "Sum of total_amount over incident orders."),
        "units_affected": metric(units, "Units ordered across incident orders."),
        "stock_shortage_units": metric(max(units - affected_stock_available, 0),
                                       "Units needed minus units available at the affected warehouse."),
        "transferable_units": metric(transfer_units, "Source-warehouse available minus its reorder threshold."),
        "recoverable_orders": metric(len(transfer["recovered_order_ids"]),
                                     "Incident orders fully covered by the transfer, allocated in priority order."),
        "unrecoverable_orders": metric(len(transfer["unrecovered_order_ids"]),
                                       "Incident orders still uncovered after the transfer."),
    }
