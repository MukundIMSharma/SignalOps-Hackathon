from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import AS_OF, get_db
from ..models import Order, SupportTicket
from ..schemas import OrderHealth, OrderOut

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/order-health", response_model=OrderHealth, summary="Order health summary at the demo clock")
def get_order_health(db: Session = Depends(get_db)):
    orders = [OrderOut.model_validate(o) for o in db.scalars(select(Order))]
    tickets = db.scalars(select(SupportTicket).where(SupportTicket.status == "open")).all()
    delayed = [o for o in orders if o.status == "delayed"]
    by_status: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for o in orders:
        by_status[o.status] = by_status.get(o.status, 0) + 1
    for o in delayed:
        reasons[o.delay_reason or "unknown"] = reasons.get(o.delay_reason or "unknown", 0) + 1
    return OrderHealth(
        as_of=AS_OF,
        total_orders=len(orders),
        by_status=by_status,
        delayed_orders=len(delayed),
        delayed_by_reason=reasons,
        sla_breached_orders=sum(o.sla_breached for o in orders),
        at_risk_orders=sum(o.shipment_id is None and not o.sla_breached for o in delayed),
        delayed_order_value=round(sum(o.total_amount for o in delayed), 2),
        open_tickets=len(tickets),
        open_delay_tickets=sum(t.category == "delivery_delay" for t in tickets),
    )
