# common

Shared route-layer utilities.

## Files

- `config.py`: login callbacks, permission decorators, verification decorators, path helpers
- `redis_client.py`: Redis client singleton

## Scope

- Keep only shared infrastructure or decorators here.
- Do not place feature-specific logic in this package.
