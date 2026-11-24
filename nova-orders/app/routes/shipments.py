from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Shipment
from ..schemas import Page, ShipmentOut

router = APIRouter(tags=["shipments"])


@router.get("/shipments", response_model=Page[ShipmentOut], summary="List shipments; filter by order, status or carrier")
def get_shipment_status(
    order_id: str | None = None,
    status: str | None = Query(None, description="in_transit | delivered | exception"),
    carrier: str | None = None,
    limit: int = Query(200, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List shipments; filter by order, status or carrier."""
    stmt = select(Shipment)
    for col, val in ((Shipment.order_id, order_id), (Shipment.status, status), (Shipment.carrier, carrier)):
        if val is not None:
            stmt = stmt.where(col == val)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Shipment.shipment_id).limit(limit).offset(offset)).all()
    return Page[ShipmentOut](items=rows, total=total, limit=limit, offset=offset)
