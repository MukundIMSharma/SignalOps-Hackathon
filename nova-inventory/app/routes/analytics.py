from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import AS_OF, get_db
from ..models import Product, Stock, SyncStatus, Warehouse
from ..schemas import StockHealth

router = APIRouter(tags=["analytics"])


@router.get("/analytics/stock-health", response_model=StockHealth, summary="Stock and sync health summary")
def get_stock_health(db: Session = Depends(get_db)):
    """Stock and sync health summary."""
    thresholds = dict(db.execute(select(Product.product_id, Product.reorder_threshold)).all())
    stock = db.scalars(select(Stock)).all()
    warehouses = db.scalars(select(Warehouse)).all()
    failed = db.scalars(select(SyncStatus).where(SyncStatus.status == "failed")).all()
    by_status: dict[str, int] = {}
    for w in warehouses:
        by_status[w.status] = by_status.get(w.status, 0) + 1
    return StockHealth(
        as_of=AS_OF,
        products=len(thresholds),
        warehouses=len(warehouses),
        warehouses_by_status=by_status,
        total_available_units=sum(s.available_quantity for s in stock),
        total_reserved_units=sum(s.reserved_quantity for s in stock),
        low_stock_positions=sum(s.available_quantity < thresholds[s.product_id] for s in stock),
        out_of_stock_positions=sum(s.available_quantity == 0 for s in stock),
        failed_syncs=len(failed),
        products_affected_by_sync_failures=sorted({p for f in failed for p in f.affected_products}),
    )
