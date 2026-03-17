# models

SQLAlchemy model layer.

## Files

- `order_models.py`: order, order item, and item form data models
- `board_models.py`: board and board slot models
- `print_models.py`: printable PDF and page mapping models
- `payment_data.py`: payment record model
- `user_data.py`: user and auth-related models
- `order_hooks.py`: ORM protection hooks for read-only order versions
- `__init__.py`: package export surface

## Guidelines

- Keep table names, column names, and relationship names stable unless a DB migration is planned.
- Prefer moving serialization and permission logic to `services/`.
- Keep hooks focused on DB safety, not feature orchestration.
