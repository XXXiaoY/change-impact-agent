# Demo E-Commerce Microservice

A simplified e-commerce backend for testing the Change Impact Analysis Agent.

## Services

- **OrderService** — Order lifecycle (create, pay, cancel). Depends on PaymentService and InventoryService.
- **PaymentService** — Payment processing and refunds. Interacts with PaymentGateway.
- **InventoryService** — Stock management and reservations.

## API Endpoints

- **OrderEndpoint** — REST handlers for order operations.
- **RefundEndpoint** — REST handlers for refund requests. **Note: no tests exist for this endpoint.**

## Dependency Graph

```
OrderEndpoint ──→ OrderService ──→ PaymentService ──→ PaymentGateway
                                 └→ InventoryService
RefundEndpoint ──→ OrderService
               └─→ PaymentService
```

## Known Issues

- RefundEndpoint has no test coverage
- No integration tests for the cancel → refund flow
