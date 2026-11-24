from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import AS_OF, get_db
from ..models import Order
from ..schemas import OrderOut, Page

router = APIRouter(prefix="/orders", tags=["orders"])


def paged(db: Session, stmt, limit: int, offset: int) -> Page[OrderOut]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Order.order_id).limit(limit).offset(offset)).all()
    return Page[OrderOut](items=rows, total=total, limit=limit, offset=offset)


@router.get("", response_model=Page[OrderOut], summary="List orders with filters and pagination")
def list_orders(
    status: str | None = None,
    priority: str | None = None,
    product_id: str | None = Query(None, description="SKU, e.g. SKU-104"),
    warehouse_id: str | None = None,
    customer_id: str | None = None,
    order_date_from: datetime | None = None,
    order_date_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Order)
    for col, val in ((Order.status, status), (Order.priority, priority), (Order.product_id, product_id),
                     (Order.warehouse_id, warehouse_id), (Order.customer_id, customer_id)):
        if val is not None:
            stmt = stmt.where(col == val)
    if order_date_from:
        stmt = stmt.where(Order.order_date >= order_date_from)
    if order_date_to:
        stmt = stmt.where(Order.order_date <= order_date_to)
    return paged(db, stmt, limit, offset)


@router.get("/delayed", response_model=Page[OrderOut], summary="Delayed orders (any cause)")
def get_delayed_orders(
    product_id: str | None = None,
    warehouse_id: str | None = None,
    delay_reason: str | None = Query(None, description="stock_allocation_failed | carrier_exception"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Order).where(Order.status == "delayed")
    for col, val in ((Order.product_id, product_id), (Order.warehouse_id, warehouse_id),
                     (Order.delay_reason, delay_reason)):
        if val is not None:
            stmt = stmt.where(col == val)
    return paged(db, stmt, limit, offset)


@router.get("/at-risk", response_model=Page[OrderOut],
            summary="Delayed, undispatched orders whose dispatch date has not passed yet (will breach SLA if not unblocked)")
def get_at_risk_orders(limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0),
                   db: Session = Depends(get_db)):
    stmt = select(Order).where(
        Order.status == "delayed", Order.shipment_id.is_(None), Order.expected_dispatch_date >= AS_OF
    )
    return paged(db, stmt, limit, offset)


@router.get("/{order_id}", response_model=OrderOut, summary="Order detail")
def get_order_details(order_id: str, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, f"Order {order_id} not found")
    return order
