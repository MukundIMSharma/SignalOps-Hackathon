"""Deterministic NovaCommerce orders seed. Counts must match docs/DEMO_STATE.md.

Run `python -m app.seed` to drop and recreate the database.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Customer, Order, Shipment, SupportTicket

PRICES = {"SKU-101": 89.0, "SKU-102": 49.0, "SKU-103": 219.0, "SKU-104": 129.0,
          "SKU-105": 35.0, "SKU-106": 159.0, "SKU-107": 24.0, "SKU-108": 299.0}

FIRST = ["Aria", "Bilal", "Chen", "Dara", "Elif", "Farid", "Greta", "Hiro", "Isla", "Jonas",
         "Kavya", "Liam", "Mira", "Nikhil", "Olga", "Priya", "Quinn", "Rafa", "Sana", "Tomas"]
LAST = ["Holt", "Varga", "Okafor", "Lind", "Mehta"]

VIPS = {"C-1003", "C-1008", "C-1015", "C-1021", "C-1029", "C-1036"}
DELAY_TICKET_CUSTOMERS = ["C-1002", "C-1003", "C-1005", "C-1008", "C-1010",
                          "C-1013", "C-1016", "C-1019", "C-1023"]
# 24 affected customers; four of them have a second incident order.
INCIDENT_CUSTOMERS = [f"C-{1000 + n}" for n in range(1, 25)] + ["C-1003", "C-1006", "C-1011", "C-1018"]
QTY_CYCLE = [1, 2, 3, 2]
NORMAL_SKUS = ["SKU-101", "SKU-102", "SKU-103", "SKU-105", "SKU-106", "SKU-107", "SKU-108", "SKU-104"]


def cid(n: int) -> str:
    return f"C-{1000 + n}"


def build_customers() -> list[Customer]:
    prefs = ["email", "phone", "sms"]
    out = []
    for n in range(1, 41):
        c = cid(n)
        name = f"{FIRST[(n - 1) % 20]} {LAST[(n - 1) // 8]}"
        out.append(Customer(customer_id=c, name=name, tier="vip" if c in VIPS else "standard",
                            contact_preference=prefs[n % 3], priority_flag=c in VIPS))
    return out


def build_orders() -> list[dict]:
    """Return order dicts without IDs; IDs are assigned afterwards in order_date order."""
    rows = []
    # 28 incident orders: SKU-104 at W1, allocation failed after the 2026-11-23T09:42 sync failure.
    for i, c in enumerate(INCIDENT_CUSTOMERS):
        if i < 12:  # will be past dispatch date at AS_OF
            od = datetime(2026, 11, 22, 8, 0) + timedelta(hours=2 * i)
        else:  # at risk, dispatch date still ahead
            od = datetime(2026, 11, 23, 10, 30) + timedelta(minutes=90 * (i - 12))
        rows.append(dict(customer_id=c, product_id="SKU-104", quantity=QTY_CYCLE[i % 4], order_date=od,
                         expected_dispatch_date=od + timedelta(hours=26), status="delayed",
                         delay_reason="stock_allocation_failed", warehouse_id="W1", ship=None))
    # 2 unrelated delays: dispatched on time from W2, then a carrier exception.
    for c, hour in (("C-1027", 10), ("C-1033", 14)):
        od = datetime(2026, 11, 21, hour, 0)
        rows.append(dict(customer_id=c, product_id="SKU-102", quantity=1, order_date=od,
                         expected_dispatch_date=od + timedelta(hours=24), status="delayed",
                         delay_reason="carrier_exception", warehouse_id="W2", ship="exception"))
    # 30 normal orders.
    for k in range(30):
        if k < 28:
            od = datetime(2026, 11, 15, 9, 0) + timedelta(hours=6 * k)
            status = "delivered" if k < 20 else "shipped"
        else:
            od = datetime(2026, 11, 24, 8 + (k - 28), 0)
            status = "processing"
        rows.append(dict(customer_id=cid(25 + k % 16), product_id=NORMAL_SKUS[k % 8], quantity=1 + k % 2,
                         order_date=od, expected_dispatch_date=od + timedelta(hours=24), status=status,
                         delay_reason=None, warehouse_id="W1" if k % 3 else "W2",
                         ship=status if status in ("delivered", "shipped") else None))
    rows.sort(key=lambda r: r["order_date"])
    return rows


def seed(db: Session) -> None:
    db.add_all(build_customers())
    db.flush()
    first_incident_order: dict[str, str] = {}
    for n, r in enumerate(build_orders(), start=1):
        oid = f"O-{1000 + n}"
        ship_kind = r.pop("ship")
        price = PRICES[r["product_id"]]
        sid = f"S-{2000 + n}" if ship_kind else None
        priority = "high" if r["customer_id"] in VIPS else "normal"
        db.add(Order(order_id=oid, unit_price=price, total_amount=round(price * r["quantity"], 2),
                     priority=priority, shipment_id=sid, **r))
        if r["delay_reason"] == "stock_allocation_failed":
            first_incident_order.setdefault(r["customer_id"], oid)
        if ship_kind:
            created = r["expected_dispatch_date"] - timedelta(hours=2)
            if ship_kind == "delivered":
                exp = created + timedelta(hours=48)
                db.add(Shipment(shipment_id=sid, order_id=oid, carrier="SwiftParcel", status="delivered",
                                created_at=created, expected_delivery=exp,
                                actual_delivery=exp - timedelta(hours=3), tracking_status="Delivered"))
            elif ship_kind == "shipped":
                db.add(Shipment(shipment_id=sid, order_id=oid, carrier="SwiftParcel", status="in_transit",
                                created_at=created, expected_delivery=created + timedelta(hours=96),
                                actual_delivery=None, tracking_status="In transit"))
            else:
                db.add(Shipment(shipment_id=sid, order_id=oid, carrier="NorthLine Freight", status="exception",
                                created_at=created, expected_delivery=created + timedelta(hours=40),
                                actual_delivery=None,
                                tracking_status="Carrier exception: sorting facility backlog"))
    db.flush()
    for n, c in enumerate(DELAY_TICKET_CUSTOMERS):
        oid = first_incident_order[c]
        db.add(SupportTicket(ticket_id=f"T-{3001 + n}", customer_id=c, order_id=oid, category="delivery_delay",
                             status="open", subject=f"Order {oid} has not shipped yet",
                             created_at=datetime(2026, 11, 24, 8, 0) + timedelta(minutes=20 * n)))
    db.add(SupportTicket(ticket_id="T-3010", customer_id="C-1027", order_id=None, category="billing",
                         status="open", subject="Charged twice for last month's order",
                         created_at=datetime(2026, 11, 23, 16, 0)))
    db.add(SupportTicket(ticket_id="T-3011", customer_id="C-1031", order_id=None, category="product_question",
                         status="closed", subject="Is SKU-108 compatible with older chargers?",
                         created_at=datetime(2026, 11, 20, 11, 0)))
    db.commit()


def reset() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    reset()
    print("orders database reset and seeded")
