from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from .database import AS_OF

NOT_DISPATCHED = {"pending", "processing", "delayed"}


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerOut(ORM):
    customer_id: str
    name: str
    tier: str
    contact_preference: str
    priority_flag: bool


class OrderOut(ORM):
    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    order_date: datetime
    expected_dispatch_date: datetime
    status: str
    delay_reason: str | None
    priority: str
    unit_price: float
    total_amount: float
    warehouse_id: str
    shipment_id: str | None

    @computed_field
    @property
    def sla_breached(self) -> bool:
        """Dispatch SLA: no shipment yet and past expected_dispatch_date at the demo clock (DEMO_AS_OF)."""
        return self.status in NOT_DISPATCHED and self.shipment_id is None and self.expected_dispatch_date < AS_OF

    @computed_field
    @property
    def days_overdue(self) -> int:
        return (AS_OF - self.expected_dispatch_date).days + 1 if self.sla_breached else 0


class ShipmentOut(ORM):
    shipment_id: str
    order_id: str
    carrier: str
    status: str
    created_at: datetime
    expected_delivery: datetime
    actual_delivery: datetime | None
    tracking_status: str


class TicketOut(ORM):
    ticket_id: str
    customer_id: str
    order_id: str | None
    category: str
    status: str
    subject: str
    created_at: datetime


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    as_of: datetime = AS_OF


class OrderHealth(BaseModel):
    as_of: datetime
    total_orders: int
    by_status: dict[str, int]
    delayed_orders: int
    delayed_by_reason: dict[str, int]
    sla_breached_orders: int
    at_risk_orders: int
    delayed_order_value: float
    open_tickets: int
    open_delay_tickets: int


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
