from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer, Order
from ..schemas import CustomerOut, OrderOut, Page
from .orders import paged

router = APIRouter(tags=["customers"])


def require_customer(db: Session, customer_id: str) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, f"Customer {customer_id} not found")
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerOut, summary="Customer details")
def get_customer_details(customer_id: str, db: Session = Depends(get_db)):
    return require_customer(db, customer_id)


@router.get("/customers/{customer_id}/orders", response_model=Page[OrderOut], summary="Customer order history")
def get_customer_orders(customer_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                    db: Session = Depends(get_db)):
    require_customer(db, customer_id)
    return paged(db, select(Order).where(Order.customer_id == customer_id), limit, offset)
