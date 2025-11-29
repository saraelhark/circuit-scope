
# FastAPI backend

This folder contains the FastAPI backend for Circuit Scope. It handles authentication, project uploads, KiCad processing, and the public API.

## Project structure

``` markdown
app/
  api/         # FastAPI routers
  core/        # configuration and shared utilities
  main.py      # application factory
db/
  models.py    # SQLAlchemy ORM models
  sessions.py  # async session dependency
```

## Running via Docker Compose (recommended)

From the repository root, see the main `README.md` for details:

```bash
docker compose up --build
```

The backend container includes KiCad 9 and `kicad-cli` and exposes the API on port `8000`.

## Local development without Docker

1. **Install uv** (if not already installed):

   ```bash
   pip install uv
   ```

2. **Install dependencies** using `pyproject.toml`:

   ```bash
   uv sync
   ```

   This creates a virtual environment and installs the dependencies listed in `pyproject.toml`.

3. **Create a local environment file**:

   ```bash
   cp .env.example .env
   ```

   Important variables:

   - `DATABASE_URL` — async SQLAlchemy URL (e.g. Neon connection string).
   - `CORS_ORIGINS` — allowed frontend origins.
   - `FRONTEND_SECRET_KEY` — must match `NUXT_PRIVATE_FRONTEND_SECRET_KEY` in the frontend.
   - `STORAGE_BACKEND`, `STORAGE_LOCAL_BASE_PATH` — where generated assets are stored.

4. **Run the API locally**:

   ```bash
   uv run uvicorn app.main:create_app --factory --reload
   ```

   The API will be available on `http://localhost:8000` by default.

## Database migrations

Alembic is configured for async SQLAlchemy. Existing revisions live under `alembic/versions`.

Common commands:

```bash
# Create a new migration after updating models
uv run alembic revision --autogenerate -m "describe change"

# Apply migrations
uv run alembic upgrade head
```

Ensure the database specified in `DATABASE_URL` is reachable before running migrations.

## KiCad CLI usage

The backend uses **KiCad 9** and `kicad-cli` to generate preview assets for schematics, PCB layers, and 3D models. In containers, KiCad is installed via the backend `Dockerfile`. For local development without Docker, install KiCad 9+ and ensure `kicad-cli` is available on your `PATH`.

Configuration is controlled by:

- `KICAD_CLI_PATH` — path to the `kicad-cli` executable (default: `kicad-cli`).
- `KICAD_CLI_TIMEOUT_SECONDS` — max seconds to wait for each command (default: `120`).

The service `app/services/previews.py` invokes the following commands.

### Schematic → SVG

All schematic sheets are exported as SVGs, then combined into a single "all sheets" view to make it easier to review:

```bash
kicad-cli sch export svg \
  --output ./out/schematics \
  --exclude-drawing-sheet \
  --no-background-color \
  project/main.kicad_sch
```

Key flags:

- `--output` — target directory for generated SVGs.
- `--exclude-drawing-sheet` — omit title block / frame.
- `--no-background-color` — keep a transparent background for web rendering.

### PCB → SVG (front, back, inner layers)

Front and back layers (as used by the preview service):

```bash
# Front
kicad-cli pcb export svg \
  --output ./out/layouts/front.svg \
  --layers F.Cu,F.Mask,F.SilkS,Edge.Cuts,User.Drawings \
  --exclude-drawing-sheet \
  --page-size-mode 2 \
  project/board.kicad_pcb

# Back
kicad-cli pcb export svg \
  --output ./out/layouts/back.svg \
  --layers B.Cu,B.Mask,B.SilkS,Edge.Cuts,User.Drawings \
  --exclude-drawing-sheet \
  --page-size-mode 2 \
  project/board.kicad_pcb
```

Inner copper layers are generated with the same pattern using `In1.Cu` ... `In6.Cu` plus `Edge.Cuts` and `User.Drawings`.
This is working for boards with up to 8 layers.

### PCB → GLB (3D model)

The 3D model used in the viewer is produced via:

```bash
kicad-cli pcb export glb \
  --output ./out/models/board.glb \
  --include-tracks \
  --include-pads \
  --include-zones \
  --include-silkscreen \
  --include-soldermask \
  --subst-models \
  project/board.kicad_pcb
```

The backend image configures KiCad so that standard 3D models are available (see `KICAD9_3DMODEL_DIR` in the Dockerfile). Custom or non-standard 3D models are not gonna be included.
