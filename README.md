# Circuit Scope

## Backend container

1. Copy `backend/.env.example` to `backend/.env` and adjust values (DB URL, KiCad CLI path/timeout, etc.).
2. Build and run the services:

   ```bash
   docker compose up --build
   ```

   This starts:

   - `backend`: FastAPI app served by uvicorn on http://localhost:8000

   Volumes mount the backend source code (`./backend/app`) for live reload and `./backend/var/storage` for generated previews.

3. To stop the stack:

   ```bash
   docker compose down
   ```

4. Logs:

   ```bash
   docker compose logs -f backend
   ```

5. Database: configure `DATABASE_URL` in `backend/.env` to point at your Neon instance (e.g. `postgresql+asyncpg://...neon.tech/...`). No database container is included; the backend connects to Neon directly.
