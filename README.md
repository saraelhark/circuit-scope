# Circuit Scope

## WIP: still implementing the basic functionality and setting up the structure

This is meant to be a free, open source platform where people can upload their electronic hardware projects and crowdsource reviews from other people.
Right now this supports KiCad projects, as most people who do electronics hardware hobby projects use KiCad.
If your project is secret due to IP or other reasons this is not the right place for you ;)

## Run locally with Docker Compose

1. **Prerequisites**

   - Docker and Docker Compose v2+

2. **Clone the repository**

   ```bash
   git clone https://github.com/saraelhark/circuit-scope.git
   cd circuit-scope
   ```

3. **Create environment files**

   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

   - Set `DATABASE_URL` in `backend/.env` to your Postgres/Neon connection string.
   - Ensure `FRONTEND_SECRET_KEY` in `backend/.env` matches `NUXT_PRIVATE_FRONTEND_SECRET_KEY` in `frontend/.env`.
   - Set OAuth client IDs/secrets in `frontend/.env` if you want to log in with Google/GitHub locally.

4. **Start the stack**

   From the repository root:

   ```bash
   docker compose up --build
   ```

   This will build and start:

   - `backend` (FastAPI API) on `http://localhost:8000`
   - `frontend` (Nuxt 3 / Nitro) on `http://localhost:3000`

5. **Stop the stack**

   ```bash
   docker compose down
   ```

## License

This project is licensed under the Apache License 2.0. See `LICENSE` for details.
