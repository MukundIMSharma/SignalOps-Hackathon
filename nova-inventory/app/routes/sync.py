from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SyncStatus
from ..schemas import Page, SyncStatusOut

router = APIRouter(tags=["sync"])


@router.get("/sync/status", response_model=Page[SyncStatusOut],
            summary="Inventory synchronization status per warehouse source, including errors and affected SKUs")
def get_inventory_sync_status(status: str | None = Query(None, description="success | failed"),
                              warehouse_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(SyncStatus)
    if status:
        stmt = stmt.where(SyncStatus.status == status)
    if warehouse_id:
        stmt = stmt.where(SyncStatus.warehouse_id == warehouse_id)
    rows = db.scalars(stmt.order_by(SyncStatus.sync_id)).all()
    return Page[SyncStatusOut](items=rows, total=len(rows), limit=len(rows), offset=0)
