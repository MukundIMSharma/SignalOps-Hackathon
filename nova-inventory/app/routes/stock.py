from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Stock
from ..schemas import LowStockOut, Page, ProductStockOut, StockOut

router = APIRouter(tags=["stock"])


@router.get("/stock", response_model=Page[StockOut], summary="Stock positions; filter by product or warehouse")
def get_warehouse_inventory(product_id: str | None = None, warehouse_id: str | None = None,
                            limit: int = Query(200, ge=1, le=200), offset: int = Query(0, ge=0),
                            db: Session = Depends(get_db)):
    """Stock positions; filter by product or warehouse."""
    stmt = select(Stock)
    if product_id:
        stmt = stmt.where(Stock.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(Stock.warehouse_id == warehouse_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Stock.product_id, Stock.warehouse_id).limit(limit).offset(offset)).all()
    return Page[StockOut](items=rows, total=total, limit=limit, offset=offset)


@router.get("/stock/low", response_model=Page[LowStockOut],
            summary="Stock positions with available quantity below the product's reorder threshold")
def get_low_stock_products(warehouse_id: str | None = None, db: Session = Depends(get_db)):
    """Stock positions with available quantity below the product's reorder threshold."""
    stmt = (select(Stock, Product.reorder_threshold).join(Product)
            .where(Stock.available_quantity < Product.reorder_threshold))
    if warehouse_id:
        stmt = stmt.where(Stock.warehouse_id == warehouse_id)
    items = [LowStockOut(**StockOut.model_validate(s).model_dump(), reorder_threshold=t,
                         shortfall=t - s.available_quantity)
             for s, t in db.execute(stmt.order_by(Stock.product_id, Stock.warehouse_id))]
    return Page[LowStockOut](items=items, total=len(items), limit=len(items), offset=0)


@router.get("/stock/{product_id}", response_model=ProductStockOut, summary="Stock for one product across all warehouses")
def get_product_stock(product_id: str, db: Session = Depends(get_db)):
    """Stock for one product across all warehouses."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, f"Product {product_id} not found")
    rows = db.scalars(select(Stock).where(Stock.product_id == product_id).order_by(Stock.warehouse_id)).all()
    return ProductStockOut(product_id=product_id, reorder_threshold=product.reorder_threshold,
                           total_available=sum(s.available_quantity for s in rows),
                           total_reserved=sum(s.reserved_quantity for s in rows), warehouses=rows)
