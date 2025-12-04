#!/bin/bash
set -e

# Usage: ./deploy.sh <user> <host>
# Example: ./deploy.sh deploy server-ip-or-hostname

SSH_USER=${1:-deploy}
SSH_HOST=${2:-your-server-ip}
TARGET_DIR="/srv/circuitscope"

echo "🚀 Starting deployment to $SSH_USER@$SSH_HOST..."

# 1. Validate required environment variables
REQUIRED_VARS=(
  "ACME_EMAIL"
  "DATABASE_URL"
  "NUXT_AUTH_SECRET"
  "FRONTEND_SECRET_KEY"
  "NUXT_PRIVATE_FRONTEND_SECRET_KEY"
  "NUXT_PRIVATE_GOOGLE_CLIENT_ID"
  "NUXT_PRIVATE_GOOGLE_CLIENT_SECRET"
  "NUXT_PRIVATE_GITHUB_CLIENT_ID"
  "NUXT_PRIVATE_GITHUB_CLIENT_SECRET"
)

for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo "❌ Error: Environment variable $VAR is not set."
    echo "Please export it before running this script."
    exit 1
  fi
done

# 2. Copy configuration files
echo "📂 Copying configuration files..."
scp deploy/docker-compose.yml deploy/Caddyfile "$SSH_USER@$SSH_HOST:$TARGET_DIR/"

# 3. Execute deployment on server
echo "⚡ Executing remote deployment..."
ssh "$SSH_USER@$SSH_HOST" "bash -s" <<EOF
  cd $TARGET_DIR

  # Create .env file
  cat <<ENV > .env
# --- Backend Config ---
APP_NAME='${APP_NAME}'
DEBUG='${DEBUG}'
API_PREFIX='${API_PREFIX}'
ACME_EMAIL='${ACME_EMAIL}'
DATABASE_URL='${DATABASE_URL}'
FRONTEND_SECRET_KEY='${FRONTEND_SECRET_KEY}'
STORAGE_BACKEND='${STORAGE_BACKEND}'
STORAGE_LOCAL_BASE_PATH='${STORAGE_LOCAL_BASE_PATH}'
CORS_ORIGINS=${CORS_ORIGINS}

# --- Frontend Config ---
NUXT_PRIVATE_BACKEND_URL='${NUXT_PRIVATE_BACKEND_URL}'
NUXT_PRIVATE_FRONTEND_SECRET_KEY='${NUXT_PRIVATE_FRONTEND_SECRET_KEY}'
NUXT_AUTH_SECRET='${NUXT_AUTH_SECRET}'
AUTH_ORIGIN='${AUTH_ORIGIN}'
NUXT_PRIVATE_GOOGLE_CLIENT_ID='${NUXT_PRIVATE_GOOGLE_CLIENT_ID}'
NUXT_PRIVATE_GOOGLE_CLIENT_SECRET='${NUXT_PRIVATE_GOOGLE_CLIENT_SECRET}'
NUXT_PRIVATE_GITHUB_CLIENT_ID='${NUXT_PRIVATE_GITHUB_CLIENT_ID}'
NUXT_PRIVATE_GITHUB_CLIENT_SECRET='${NUXT_PRIVATE_GITHUB_CLIENT_SECRET}'
NUXT_PUBLIC_POSTHOG_PUBLIC_KEY='${NUXT_PUBLIC_POSTHOG_PUBLIC_KEY}'
NUXT_PUBLIC_POSTHOG_HOST='${NUXT_PUBLIC_POSTHOG_HOST}'

# --- Docker Config ---
GITHUB_REPOSITORY_OWNER='${GITHUB_REPOSITORY_OWNER}'
ENV

  echo "🐳 Pulling latest images..."
  docker compose pull

  # (idempotent)
  echo "📦 Running database migrations..."
  docker compose run --rm backend bash -lc "cd /app && uv run alembic upgrade head"
EOF

echo "🔄 Restarting services..."
ssh "$SSH_USER@$SSH_HOST" "cd $TARGET_DIR && docker compose up -d --remove-orphans"

echo "🧹 Cleaning up..."
ssh "$SSH_USER@$SSH_HOST" "cd $TARGET_DIR && docker image prune -f"

echo "✅ Deployment complete!"
