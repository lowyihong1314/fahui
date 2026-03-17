# print_paiwei

Paiwei generation and file-serving feature.

## Files

- `blueprint.py`: shared blueprint object
- `router.py`: package entry that imports route modules
- `file_routes.py`: file download, preview, and generation routes
- `config_routes.py`: point JSON config routes
- `generator.py`: PDF generation and merge logic
- `points.py`: point config load/save helpers
- `service.py`: small helper functions used by the feature

## Scope

- paiwei PDF generation
- QR/barcode-aware printable output
- cached image rendering
- point config management
