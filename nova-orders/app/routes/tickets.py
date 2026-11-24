from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SupportTicket
from ..schemas import Page, TicketOut

router = APIRouter(prefix="/tickets", tags=["support tickets"])


@router.get("", response_model=Page[TicketOut], summary="Support tickets; filter by customer, order, category, status")
def get_support_tickets(
    customer_id: str | None = None,
    order_id: str | None = None,
    category: str | None = Query(None, description="delivery_delay | billing | product_question"),
    status: str | None = Query(None, description="open | closed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(SupportTicket)
    for col, val in ((SupportTicket.customer_id, customer_id), (SupportTicket.order_id, order_id),
                     (SupportTicket.category, category), (SupportTicket.status, status)):
        if val is not None:
            stmt = stmt.where(col == val)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(SupportTicket.ticket_id).limit(limit).offset(offset)).all()
    return Page[TicketOut](items=rows, total=total, limit=limit, offset=offset)
