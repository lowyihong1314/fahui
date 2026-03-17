# app

Backend application package.

## Contents

- `__init__.py`: Flask app factory and blueprint registration
- `config.py`: runtime config
- `extensions.py`: shared Flask extensions
- `models/`: ORM layer
- `services/`: domain services
- `function/`: feature route packages
- `database/`: local runtime assets and generated files

## Rules

- Keep route registration in `app/__init__.py`.
- Put shared business logic in `services/` when multiple features use it.
- Keep feature-specific logic inside the matching `function/<feature>/` package.
- Do not add new work to the legacy template flow unless strictly required.
