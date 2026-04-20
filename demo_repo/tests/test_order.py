"""Tests for OrderService."""

from src.services.order_service import OrderService


def test_create_order_success():
    service = OrderService()
    service.inventory_service.restock("ITEM-1", 10)

    order = service.create_order(
        customer_id="CUST-001",
        items=[{"item_id": "ITEM-1", "quantity": 2}],
        total_amount=50.0,
    )
    assert order.order_id.startswith("ORD-")
    assert order.status.value == "confirmed"


def test_cancel_order():
    service = OrderService()
    service.inventory_service.restock("ITEM-1", 10)

    order = service.create_order(
        customer_id="CUST-001",
        items=[{"item_id": "ITEM-1", "quantity": 2}],
        total_amount=50.0,
    )
    cancelled = service.cancel_order(order.order_id)
    assert cancelled.status.value == "cancelled"
    # Stock should be released
    assert service.inventory_service.check_stock("ITEM-1") == 10
