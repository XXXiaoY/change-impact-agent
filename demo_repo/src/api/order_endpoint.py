"""Order endpoint - handles order creation, payment, and cancellation."""

from src.services.order_service import OrderService


class OrderEndpoint:
    def __init__(self):
        self.order_service = OrderService()

    def create_order(self, customer_id: str, items: list[dict], total_amount: float, currency: str = "USD") -> dict:
        """Create a new order."""
        order = self.order_service.create_order(customer_id, items, total_amount, currency)
        return {
            "success": True,
            "order_id": order.order_id,
            "status": order.status.value,
        }

    def pay_order(self, order_id: str) -> dict:
        """Process payment for an order."""
        order = self.order_service.pay_order(order_id)
        return {
            "success": True,
            "order_id": order.order_id,
            "status": order.status.value,
        }

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an order."""
        order = self.order_service.cancel_order(order_id)
        return {
            "success": True,
            "order_id": order.order_id,
            "status": order.status.value,
        }

    def get_order(self, order_id: str) -> dict:
        """Get order details."""
        order = self.order_service.get_order(order_id)
        return {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status.value,
        }
