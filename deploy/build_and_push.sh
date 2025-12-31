#!/bin/bash
set -e

# Usage: ./deploy/build_and_push.sh [github_username]
# Example: ./deploy/build_and_push.sh saraelhark

GITHUB_USER=${1:?Usage: $0 <dockerhub-username>}
REPO_NAME="circuit-scope"

echo "🐳 Logging into GitHub Container Registry..."
echo "Make sure you have a PAT with write:packages scope!"
if ! echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin; then
  echo "Login via env var failed, trying manual login..."
  docker login ghcr.io
fi

echo "🔨 Building Backend..."
docker build --platform linux/amd64 -t ghcr.io/$GITHUB_USER/$REPO_NAME-backend:latest ./backend

echo "🔨 Building Frontend..."
docker build --platform linux/amd64 -t ghcr.io/$GITHUB_USER/$REPO_NAME-frontend:latest ./frontend

echo "🚀 Pushing Backend..."
docker push ghcr.io/$GITHUB_USER/$REPO_NAME-backend:latest

echo "🚀 Pushing Frontend..."
docker push ghcr.io/$GITHUB_USER/$REPO_NAME-frontend:latest

echo "✅ Build and Push Complete!"
