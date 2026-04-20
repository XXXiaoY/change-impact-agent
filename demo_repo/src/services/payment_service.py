"""Payment service - handles payment processing, refunds, and gateway interactions."""

from src.models.order import Order, Refund, RefundStatus
from src.utils.validation import validate_positive_amount, validate_currency


class PaymentGatewayError(Exception):
    pass


class PaymentGateway:
    """External payment gateway client."""

    def charge(self, order_id: str, amount: float, currency: str) -> str:
        """Charge customer. Returns transaction ID."""
        # In production, this calls external payment API
        return f"TXN-{order_id}"

    def submit_refund(self, transaction_id: str, amount: float, currency: str) -> str:
        """Submit refund to gateway. Returns refund transaction ID."""
        return f"REF-{transaction_id}"


class PaymentService:
    def __init__(self):
        self.gateway = PaymentGateway()

    def process_payment(self, order: Order) -> str:
        """Process payment for an order. Returns transaction ID."""
        validate_positive_amount(order.total_amount)
        validate_currency(order.currency)

        transaction_id = self.gateway.charge(
            order.order_id, order.total_amount, order.currency
        )
        return transaction_id

    def process_refund(self, order: Order, refund: Refund) -> Refund:
        """Process a refund for an order."""
        validate_positive_amount(refund.amount)
        self._validate_refund_amount(order, refund)

        transaction_id = f"TXN-{order.order_id}"
        self.gateway.submit_refund(
            transaction_id, refund.amount, order.currency
        )

        refund.status = RefundStatus.PROCESSED
        return refund

    def _validate_refund_amount(self, order: Order, refund: Refund) -> None:
        """Ensure refund amount does not exceed order total."""
        if refund.amount > order.total_amount:
            raise ValueError(
                f"Refund amount {refund.amount} exceeds order total {order.total_amount}"
            )

    def get_payment_status(self, transaction_id: str) -> str:
        """Check payment status from gateway."""
        # Simplified - would call gateway API
        return "completed"
