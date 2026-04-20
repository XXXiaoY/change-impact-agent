"""Refund endpoint - handles refund requests from customers."""

from src.models.order import Refund
from src.services.payment_service import PaymentService
from src.services.order_service import OrderService


class RefundEndpoint:
    def __init__(self):
        self.order_service = OrderService()
        self.payment_service = PaymentService()

    def handle_refund(self, order_id: str, amount: float, reason: str = "") -> dict:
        """Process a refund request."""
        order = self.order_service.get_order(order_id)

        if not order.is_refundable():
            return {
                "success": False,
                "error": f"Order {order_id} is not eligible for refund",
            }

        refund = Refund(
            refund_id=f"REF-{order_id}",
            order_id=order_id,
            amount=amount,
            reason=reason,
        )

        result = self.payment_service.process_refund(order, refund)
        return {
            "success": True,
            "refund_id": result.refund_id,
            "status": result.status.value,
        }

    def get_refund_status(self, refund_id: str) -> dict:
        """Check status of a refund."""
        # Simplified - would query database
        return {"refund_id": refund_id, "status": "processed"}
