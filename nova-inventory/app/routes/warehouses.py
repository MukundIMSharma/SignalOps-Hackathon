from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Warehouse
from ..schemas import Page, WarehouseOut

router = APIRouter(tags=["warehouses"])


@router.get("/warehouses", response_model=Page[WarehouseOut], summary="Warehouses and their operational status")
def get_warehouse_status(db: Session = Depends(get_db)):
    rows = db.scalars(select(Warehouse).order_by(Warehouse.warehouse_id)).all()
    return Page[WarehouseOut](items=rows, total=len(rows), limit=len(rows), offset=0)
