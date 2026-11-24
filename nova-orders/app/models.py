from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    tier: Mapped[str]  # standard | vip
    contact_preference: Mapped[str]  # email | phone | sms
    priority_flag: Mapped[bool]


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    product_id: Mapped[str] = mapped_column(index=True)
    quantity: Mapped[int]
    order_date: Mapped[datetime]
    expected_dispatch_date: Mapped[datetime]
    status: Mapped[str] = mapped_column(index=True)  # pending|processing|delayed|shipped|delivered|cancelled
    delay_reason: Mapped[str | None]  # stock_allocation_failed | carrier_exception
    priority: Mapped[str]  # normal | high
    unit_price: Mapped[float]
    total_amount: Mapped[float]
    warehouse_id: Mapped[str] = mapped_column(index=True)
    shipment_id: Mapped[str | None]


class Shipment(Base):
    __tablename__ = "shipments"
    shipment_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), index=True)
    carrier: Mapped[str]
    status: Mapped[str]  # in_transit | delivered | exception
    created_at: Mapped[datetime]
    expected_delivery: Mapped[datetime]
    actual_delivery: Mapped[datetime | None]
    tracking_status: Mapped[str]


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    ticket_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    order_id: Mapped[str | None]
    category: Mapped[str]  # delivery_delay | billing | product_question
    status: Mapped[str]  # open | closed
    subject: Mapped[str]
    created_at: Mapped[datetime]
