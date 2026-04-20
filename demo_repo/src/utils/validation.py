"""Shared validation utilities used across services."""


class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def validate_positive_amount(amount: float) -> None:
    """Validate that an amount is positive."""
    if amount <= 0:
        raise ValidationError(f"Amount must be positive, got {amount}")


def validate_currency(currency: str) -> None:
    """Validate that currency code is supported."""
    supported = {"USD", "EUR", "GBP", "JPY", "CNY"}
    if currency not in supported:
        raise ValidationError(f"Unsupported currency: {currency}")


def validate_order_id(order_id: str) -> None:
    """Validate order ID format."""
    if not order_id or not order_id.startswith("ORD-"):
        raise ValidationError(f"Invalid order ID format: {order_id}")


def validate_customer_id(customer_id: str) -> None:
    """Validate customer ID is not empty."""
    if not customer_id or not customer_id.strip():
        raise ValidationError("Customer ID cannot be empty")
