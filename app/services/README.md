# services

Shared backend business services.

## Files

- `order_service.py`: order search, masking, and detail serialization
- `order_item_service.py`: order item price and print/detail serialization
- `board_service.py`: board aggregation helpers
- `payment_service.py`: payment serialization and total calculation

## Guidelines

- Put reusable business logic here when it is shared across features.
- Keep Flask route concerns out of this layer.
- Prefer returning plain dicts or simple values.
