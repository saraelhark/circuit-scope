
# FastAPI backend

## Project structure

```
app/
  api/         # FastAPI routers
  core/        # configuration and shared utilities
  main.py      # application factory
db/
  models.py    # SQLAlchemy ORM models
  sessions.py  # async session dependency
```

## Environment setup

1. Create a virtual environment:

   ```bash
   uv venv
   ```

2. Copy the sample environment and adjust values:

   ```bash
   cp .env.example .env
   ```

   Required variables:

   - `DATABASE_URL` — async SQLAlchemy URL (Neon recommended)
   - Optional CORS settings (`CORS_ORIGINS`, etc.)

3. Install dependencies when needed:

   ```bash
   uv pip install -r requirements.txt  # or use `uv pip install <pkg>`
   ```

## Running the API

```bash
uv run uvicorn app.main:create_app --reload
```

## Database migrations

Alembic is configured for async SQLAlchemy. Existing revisions live under `alembic/versions`.

Common commands:

```bash
# Create a new migration after updating models
uv run alembic revision --autogenerate -m "describe change"

# Apply migrations
uv run alembic upgrade head

# Downgrade one step (optional)
uv run alembic downgrade -1
```

Ensure the database specified in `DATABASE_URL` is reachable (e.g., Neon connection string) before running migrations.
