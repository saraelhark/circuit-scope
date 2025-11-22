# Circuit Scope

## WIP: still implementing the basic functionality and setting up the structure

## Backend container

1. Copy `backend/.env.example` to `backend/.env` and adjust values (DB URL, KiCad CLI path/timeout, etc.).
2. Build and run the services:

   ```bash
   docker compose up --build
   ```

   This starts:

   - `backend`: FastAPI app served by uvicorn on <http://localhost:8000>

   Volumes mount the backend source code (`./backend/app`) for live reload and `./backend/var/storage` for generated previews.

   Clean build

   ```bash
   docker compose build --no-cache
   ```

3. To stop the stack:

   ```bash
   docker compose down
   ```

4. Logs:

   ```bash
   docker compose logs -f backend
   ```

5. Database: configure `DATABASE_URL` in `backend/.env` to point at your Neon instance (e.g. `postgresql+asyncpg://...neon.tech/...`). No database container is included; the backend connects to Neon directly.

```bash
docker compose run --rm backend alembic upgrade head
```

## KiCad CLI quick reference

The backend uses `kicad-cli` (KiCad 9) to generate previews. Useful commands:

### Schematic to SVG

Exports every sheet as an SVG into the target directory.

```bash
kicad-cli sch export svg \
  --output ./out/schematics \
  --exclude-drawing-sheet \
  --no-background-color \
  project/connectors.kicad_sch
```

Key flags:

- `--output <dir>`: destination directory. Defaults to current dir if omitted.
- `--exclude-drawing-sheet`: omit title block / frame.
- `--no-background-color`: keep transparent background.
- `--pages <list>`: optional comma-separated list of pages to select.

### PCB to SVG

```bash
kicad-cli pcb export svg \
  --output ./out/layouts/front.svg \
  --layers F.Cu,F.Mask,F.SilkS,Edge.Cuts,User.Drawings \
  --exclude-drawing-sheet \
  --page-size-mode 2 \
  project/air-ctrl.kicad_pcb
```

- `--layers`: comma-separated set of layers to plot; must include at least one copper layer.
- `--mirror`: mirror output (useful for rendering the back side).
- `--page-size-mode 2`: fit canvas to board outline.

### PCB to GLB (3D)

```bash
kicad-cli pcb export glb \
  --output ./out/models/board.glb \
  --board-only \
  project/air-ctrl.kicad_pcb
```

General tips:

- Provide absolute paths inside Docker/CI to avoid working-directory surprises.
- Add `--define-var KEY=VALUE` to override project variables on the fly.
- Use `--theme <name>` if you rely on a custom color theme saved in your KiCad config.

## Setup local db for development TBD

## Current Limitations and notes

- Only default library components are gonna be in the 3d model
- Newer KiCAD CLI (currently 9) support old KiCAD versions (the opposite is not true).
