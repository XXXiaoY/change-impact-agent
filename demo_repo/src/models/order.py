from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class RefundStatus(Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSED = "processed"
    REJECTED = "rejected"


@dataclass
class Order:
    order_id: str
    customer_id: str
    items: list[dict]
    total_amount: float
    currency: str = "USD"
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def is_cancellable(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED)

    def is_refundable(self) -> bool:
        return self.status in (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED)


@dataclass
class Refund:
    refund_id: str
    order_id: str
    amount: float
    reason: str = ""
    status: RefundStatus = RefundStatus.REQUESTED
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
