"""Tests for PaymentService."""

from src.models.order import Order, Refund, OrderStatus
from src.services.payment_service import PaymentService
from src.utils.validation import ValidationError


def test_process_payment_success():
    service = PaymentService()
    order = Order(
        order_id="ORD-0001",
        customer_id="CUST-001",
        items=[{"item_id": "ITEM-1", "quantity": 1}],
        total_amount=99.99,
    )
    txn_id = service.process_payment(order)
    assert txn_id.startswith("TXN-")


def test_process_payment_invalid_amount():
    service = PaymentService()
    order = Order(
        order_id="ORD-0001",
        customer_id="CUST-001",
        items=[],
        total_amount=-10.0,
    )
    try:
        service.process_payment(order)
        assert False, "Should have raised"
    except ValidationError:
        pass


def test_process_refund_success():
    service = PaymentService()
    order = Order(
        order_id="ORD-0001",
        customer_id="CUST-001",
        items=[],
        total_amount=99.99,
        status=OrderStatus.PAID,
    )
    refund = Refund(
        refund_id="REF-0001",
        order_id="ORD-0001",
        amount=50.0,
    )
    result = service.process_refund(order, refund)
    assert result.status.value == "processed"


def test_refund_exceeds_order_total():
    service = PaymentService()
    order = Order(
        order_id="ORD-0001",
        customer_id="CUST-001",
        items=[],
        total_amount=50.0,
    )
    refund = Refund(
        refund_id="REF-0001",
        order_id="ORD-0001",
        amount=100.0,
    )
    try:
        service.process_refund(order, refund)
        assert False, "Should have raised"
    except ValueError:
        pass
