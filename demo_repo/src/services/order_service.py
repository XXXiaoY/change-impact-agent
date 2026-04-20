"""Order service - orchestrates order lifecycle across payment and inventory."""

from src.models.order import Order, OrderStatus, Refund, RefundStatus
from src.services.payment_service import PaymentService
from src.services.inventory_service import InventoryService
from src.utils.validation import validate_order_id, validate_customer_id, validate_positive_amount


class OrderService:
    def __init__(self):
        self.payment_service = PaymentService()
        self.inventory_service = InventoryService()
        self._orders: dict[str, Order] = {}

    def create_order(self, customer_id: str, items: list[dict], total_amount: float, currency: str = "USD") -> Order:
        """Create a new order with stock reservation."""
        validate_customer_id(customer_id)
        validate_positive_amount(total_amount)

        order_id = f"ORD-{len(self._orders) + 1:04d}"
        order = Order(
            order_id=order_id,
            customer_id=customer_id,
            items=items,
            total_amount=total_amount,
            currency=currency,
        )

        # Reserve inventory
        self.inventory_service.reserve_stock(order_id, items)
        order.status = OrderStatus.CONFIRMED
        self._orders[order_id] = order
        return order

    def pay_order(self, order_id: str) -> Order:
        """Process payment for a confirmed order."""
        order = self._get_order(order_id)

        if order.status != OrderStatus.CONFIRMED:
            raise ValueError(f"Order {order_id} is not in CONFIRMED state")

        self.payment_service.process_payment(order)
        order.status = OrderStatus.PAID
        return order

    def cancel_order(self, order_id: str) -> Order:
        """Cancel an order, releasing inventory and processing refund if paid."""
        order = self._get_order(order_id)

        if not order.is_cancellable() and order.status != OrderStatus.PAID:
            raise ValueError(f"Order {order_id} cannot be cancelled in {order.status.value} state")

        # Release inventory
        self.inventory_service.release_stock(order_id)

        # Refund if already paid
        if order.status == OrderStatus.PAID:
            refund = Refund(
                refund_id=f"REF-{order_id}",
                order_id=order_id,
                amount=order.total_amount,
                reason="Order cancelled",
            )
            self.payment_service.process_refund(order, refund)

        order.status = OrderStatus.CANCELLED
        return order

    def get_order(self, order_id: str) -> Order:
        """Public method to retrieve an order."""
        return self._get_order(order_id)

    def _get_order(self, order_id: str) -> Order:
        """Internal method to fetch and validate order exists."""
        validate_order_id(order_id)
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"Order not found: {order_id}")
        return order
