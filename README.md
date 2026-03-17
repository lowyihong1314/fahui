# FAHUI

Flask backend for the FAHUI order, payment, board, and paiwei workflow.

## Structure

- `app/`: backend application package
- `app/models/`: SQLAlchemy models and model hooks
- `app/services/`: cross-module domain services
- `app/function/`: route packages grouped by feature
- `app/database/`: local assets, templates, generated files, and uploaded payment proof
- `frontend/`: separate frontend workspace
- `templates/`: legacy Flask template files, kept only for compatibility
- `static/`: legacy static assets

## Entry Point

- App factory: `app.create_app()`
- API root prefix: `/api`

## Current Architecture

- `models` defines database entities and low-level ORM protection hooks.
- `services` contains reusable business logic and serializers.
- `function` contains feature packages with route, feature service, and helper modules.

## Maintenance Notes

- `app/function/template/` is deprecated and no longer actively maintained.
- `templates/` is deprecated and kept for backward compatibility only.
- New backend work should prefer JSON APIs plus the separate frontend instead of extending legacy Flask templates.
