from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas import Page, ProductOut

router = APIRouter(tags=["products"])


@router.get("/products", response_model=Page[ProductOut], summary="Product catalog")
def list_products(category: str | None = None, limit: int = Query(200, ge=1, le=200),
                  offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    """Product catalog."""
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Product.product_id).limit(limit).offset(offset)).all()
    return Page[ProductOut](items=rows, total=total, limit=limit, offset=offset)


@router.get("/products/{product_id}", response_model=ProductOut, summary="Product details")
def get_product_details(product_id: str, db: Session = Depends(get_db)):
    """Product details."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, f"Product {product_id} not found")
    return product
