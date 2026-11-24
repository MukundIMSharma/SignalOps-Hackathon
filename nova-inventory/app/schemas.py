from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .database import AS_OF


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductOut(ORM):
    product_id: str
    name: str
    category: str
    reorder_threshold: int


class WarehouseOut(ORM):
    warehouse_id: str
    name: str
    location: str
    status: str


class StockOut(ORM):
    product_id: str
    warehouse_id: str
    available_quantity: int
    reserved_quantity: int
    last_updated: datetime


class LowStockOut(StockOut):
    reorder_threshold: int
    shortfall: int  # reorder_threshold - available_quantity


class ProductStockOut(BaseModel):
    product_id: str
    reorder_threshold: int
    total_available: int
    total_reserved: int
    warehouses: list[StockOut]
    as_of: datetime = AS_OF


class SyncStatusOut(ORM):
    sync_id: str
    source: str
    warehouse_id: str
    status: str
    last_attempt: datetime
    last_success: datetime
    failing_since: datetime | None
    error_code: str | None
    error_message: str | None
    affected_products: list[str]
    severity: str


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    as_of: datetime = AS_OF


class StockHealth(BaseModel):
    as_of: datetime
    products: int
    warehouses: int
    warehouses_by_status: dict[str, int]
    total_available_units: int
    total_reserved_units: int
    low_stock_positions: int
    out_of_stock_positions: int
    failed_syncs: int
    products_affected_by_sync_failures: list[str]
