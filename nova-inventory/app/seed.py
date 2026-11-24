"""Deterministic NovaCommerce inventory seed. Counts must match docs/DEMO_STATE.md.

Run `python -m app.seed` to drop and recreate the database.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Product, Stock, SyncStatus, Warehouse

SYNC_FAILED_AT = datetime(2026, 11, 23, 9, 42)
LAST_GOOD_SYNC = datetime(2026, 11, 23, 9, 41)
FRESH = datetime(2026, 11, 24, 11, 30)

PRODUCTS = [  # id, name, category, reorder_threshold
    ("SKU-101", "Pulse Smart Speaker", "audio", 15),
    ("SKU-102", "Glide USB-C Hub", "accessories", 25),
    ("SKU-103", "Vista 27in Monitor", "displays", 10),
    ("SKU-104", "Aurora ANC Headphones", "audio", 20),
    ("SKU-105", "Flex Braided Cable 2m", "accessories", 40),
    ("SKU-106", "Orbit Mechanical Keyboard", "peripherals", 15),
    ("SKU-107", "Spark Phone Stand", "accessories", 15),
    ("SKU-108", "Nimbus Portable Charger", "power", 12),
]

# (product, warehouse): (available, reserved, last_updated)
STOCK = {
    ("SKU-101", "W1"): (64, 4, FRESH), ("SKU-101", "W2"): (41, 2, FRESH),
    ("SKU-102", "W1"): (120, 6, FRESH), ("SKU-102", "W2"): (88, 3, FRESH),
    ("SKU-103", "W1"): (22, 1, FRESH), ("SKU-103", "W2"): (18, 0, FRESH),
    # Incident: W1 SKU-104 frozen at 0 since the last good sync.
    ("SKU-104", "W1"): (0, 0, LAST_GOOD_SYNC), ("SKU-104", "W2"): (60, 0, FRESH),
    ("SKU-105", "W1"): (210, 10, FRESH), ("SKU-105", "W2"): (175, 5, FRESH),
    ("SKU-106", "W1"): (37, 2, FRESH), ("SKU-106", "W2"): (29, 1, FRESH),
    # Unrelated low-stock alert so "low stock" is not a one-item giveaway.
    ("SKU-107", "W1"): (52, 0, FRESH), ("SKU-107", "W2"): (8, 0, FRESH),
    ("SKU-108", "W1"): (30, 2, FRESH), ("SKU-108", "W2"): (26, 1, FRESH),
}


def seed(db: Session) -> None:
    db.add_all(Product(product_id=p, name=n, category=c, reorder_threshold=t) for p, n, c, t in PRODUCTS)
    db.add_all([
        Warehouse(warehouse_id="W1", name="Northgate Fulfillment Center", location="Northgate (fictional)",
                  status="degraded"),
        Warehouse(warehouse_id="W2", name="Riverside Distribution Hub", location="Riverside (fictional)",
                  status="operational"),
    ])
    db.flush()
    db.add_all(Stock(product_id=p, warehouse_id=w, available_quantity=a, reserved_quantity=r, last_updated=t)
               for (p, w), (a, r, t) in STOCK.items())
    db.add_all([
        SyncStatus(sync_id="SYNC-W1-WMS", source="W1-WMS", warehouse_id="W1", status="failed",
                   last_attempt=FRESH, last_success=LAST_GOOD_SYNC, failing_since=SYNC_FAILED_AT,
                   error_code="WMS_PAYLOAD_REJECTED",
                   error_message="Stock delta batch for SKU-104 rejected: schema validation failed on field "
                                 "'bin_location'; 26 retries exhausted. Availability for SKU-104 at W1 is stale.",
                   affected_products=["SKU-104"], severity="critical"),
        SyncStatus(sync_id="SYNC-W2-WMS", source="W2-WMS", warehouse_id="W2", status="success",
                   last_attempt=FRESH, last_success=FRESH, failing_since=None, error_code=None,
                   error_message=None, affected_products=[], severity="info"),
    ])
    db.commit()


def reset() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    reset()
    print("inventory database reset and seeded")
