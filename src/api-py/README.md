# OctoSupply API (Python)

FastAPI port of the OctoSupply API.

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 3000
```

Default API URL: `http://localhost:3000`

## Environment

- `PORT` (used by Makefile/uvicorn command, default `3000`)
- `DB_FILE` (default: `./data/app.db`)
- `API_CORS_ORIGINS` (comma-separated override; optional)
- `DB_MIGRATIONS_DIR` (optional override for migrations directory)

## Health checks

- `GET /api/health/live` confirms the API process is responding.
- `GET /api/health/ready` checks SQLite connectivity and returns HTTP 503 when
  the database is unavailable.

Use the readiness endpoint for startup and readiness probes, and the liveness
endpoint for liveness probes.

## Shopping cart

The cart API persists a browser-specific cart using the UUID stored by the frontend:

- `GET /api/cart/{cartId}` returns cart items, item count, and the discounted total.
- `POST /api/cart/{cartId}/items` adds `{ "productId": 1, "quantity": 2 }` (adding an existing product increases its quantity).
- `PUT /api/cart/{cartId}/items/{productId}` sets `{ "quantity": 3 }`.
- `DELETE /api/cart/{cartId}/items/{productId}` removes a product.

The cart endpoints manage cart contents only; no payment is processed.

## Database

On startup, the API applies SQL migrations from:

- `../database/migrations/*.sql`

and seeds from:

- `../database/seed/*.sql`

## OpenAPI

- OpenAPI JSON: `http://localhost:3000/openapi.json`
- Swagger UI: `http://localhost:3000/docs`
