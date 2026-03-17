# function

Feature route packages.

## Packages

- `board/`: board management routes and board command/query services
- `common/`: shared route helpers and local infrastructure clients
- `fahui/`: order search and customer creation endpoints
- `payment/`: payment APIs, quotation PDF, and receipt printing
- `print_paiwei/`: paiwei file generation, cache, and point config
- `template/`: legacy Flask template routes, deprecated
- `twilio/`: OTP send/verify flow
- `user_control/`: auth and user profile routes

## Conventions

- `router.py`: public route registration
- `service.py` or `*_service.py`: feature-local business logic
- helper modules: split by responsibility, for example `receipt.py`, `reports.py`, `points.py`

## Maintenance

- New work should not go into `template/` unless needed for compatibility.
