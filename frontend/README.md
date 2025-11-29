# Frontend (Nuxt 3)

This folder contains the Nuxt 3 / Nitro frontend. It renders the project dashboard, public review pages, SVG/3D viewers, and comment UI.

## Recommended: run via Docker Compose

From the repository root, use Docker Compose to run both frontend and backend together (see the main `README.md`):

```bash
docker compose up --build
```

The frontend will be available at `http://localhost:3000`.

## Local development without Docker

1. **Install dependencies** (Node.js 20+ recommended):

   ```bash
   npm install
   ```

2. **Create a local environment file**:

   ```bash
   cp .env.example .env
   ```

   Important variables (see comments in `.env.example`):

   - `NUXT_PRIVATE_BACKEND_URL` — internal URL the frontend uses to call the FastAPI backend.
     - In Docker, this is typically `http://backend:8000`.
     - For a locally running backend on your host, you can use `http://localhost:8000`.
   - `NUXT_PRIVATE_FRONTEND_SECRET_KEY` — must match `FRONTEND_SECRET_KEY` in the backend `.env`.
   - `NUXT_AUTH_SECRET` and `AUTH_ORIGIN` — used by the auth module.
   - OAuth client IDs/secrets for Google and GitHub login.

3. **Start the dev server**:

   ```bash
   npm run dev
   ```

   The app will be available on `http://localhost:3000`.

## Build and preview

Build the production bundle:

```bash
npm run build
```

Preview the production build locally (Nitro server using `.output`):

```bash
npm run preview
```

The `frontend/Dockerfile` uses this build output to run the app in production.
