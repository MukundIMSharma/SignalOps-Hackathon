from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    category: Mapped[str]
    reorder_threshold: Mapped[int]


class Warehouse(Base):
    __tablename__ = "warehouses"
    warehouse_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    location: Mapped[str]
    status: Mapped[str]  # operational | degraded | offline


class Stock(Base):
    __tablename__ = "stock"
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    warehouse_id: Mapped[str] = mapped_column(ForeignKey("warehouses.warehouse_id"), primary_key=True)
    available_quantity: Mapped[int]
    reserved_quantity: Mapped[int]
    last_updated: Mapped[datetime]


class SyncStatus(Base):
    __tablename__ = "sync_status"
    sync_id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str]
    warehouse_id: Mapped[str] = mapped_column(ForeignKey("warehouses.warehouse_id"))
    status: Mapped[str]  # success | failed
    last_attempt: Mapped[datetime]
    last_success: Mapped[datetime]
    failing_since: Mapped[datetime | None]
    error_code: Mapped[str | None]
    error_message: Mapped[str | None]
    affected_products: Mapped[list[str]] = mapped_column(JSON)
    severity: Mapped[str]  # info | warning | critical
