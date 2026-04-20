"""Inventory service - manages stock levels and reservations."""

from src.utils.validation import validate_positive_amount


class InsufficientStockError(Exception):
    def __init__(self, item_id: str, requested: int, available: int):
        self.item_id = item_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for {item_id}: requested {requested}, available {available}"
        )


class InventoryService:
    def __init__(self):
        # Simplified in-memory store
        self._stock: dict[str, int] = {}
        self._reservations: dict[str, list[dict]] = {}

    def check_stock(self, item_id: str) -> int:
        """Return current stock level for an item."""
        return self._stock.get(item_id, 0)

    def reserve_stock(self, order_id: str, items: list[dict]) -> bool:
        """Reserve stock for order items. Raises if insufficient."""
        for item in items:
            item_id = item["item_id"]
            quantity = item["quantity"]
            available = self.check_stock(item_id)

            if available < quantity:
                raise InsufficientStockError(item_id, quantity, available)

        # Deduct stock
        for item in items:
            item_id = item["item_id"]
            quantity = item["quantity"]
            self._stock[item_id] = self._stock.get(item_id, 0) - quantity

        self._reservations[order_id] = items
        return True

    def release_stock(self, order_id: str) -> None:
        """Release reserved stock when order is cancelled."""
        items = self._reservations.pop(order_id, [])
        for item in items:
            item_id = item["item_id"]
            quantity = item["quantity"]
            self._stock[item_id] = self._stock.get(item_id, 0) + quantity

    def restock(self, item_id: str, quantity: int) -> None:
        """Add stock for an item."""
        validate_positive_amount(quantity)
        self._stock[item_id] = self._stock.get(item_id, 0) + quantity
