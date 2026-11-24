"""Deterministic cross-system correlation: link delayed orders (Orders) to failed syncs (Inventory)."""


def link_delays_to_sync_failures(delayed_orders: list[dict], sync_statuses: list[dict]) -> dict:
    """Split delayed orders into those matching a failed sync (same SKU + warehouse) and the rest.

    A failed sync matches an order when the order's product is in the sync's affected_products and
    the order ships from the sync's warehouse.
    """
    failed = [s for s in sync_statuses if s["status"] == "failed"]
    linked: dict[str, list[dict]] = {s["sync_id"]: [] for s in failed}
    unlinked = []
    for o in delayed_orders:
        match = next((s for s in failed
                      if o["product_id"] in s["affected_products"] and o["warehouse_id"] == s["warehouse_id"]), None)
        (linked[match["sync_id"]] if match else unlinked).append(o)
    return {"linked": linked, "unlinked": unlinked, "failed_syncs": failed}


def dispatch_after_failure(orders: list[dict], failing_since: str) -> bool:
    """True when every order was due for dispatch after the sync started failing (timing supports causation)."""
    return all(o["expected_dispatch_date"] > failing_since for o in orders)
