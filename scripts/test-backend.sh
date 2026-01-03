#!/bin/bash
set -e

cd "$(dirname "$0")/../backend"

echo "==> Installing dependencies..."
uv sync --extra dev

echo "==> Running ruff check..."
uv run ruff check .

echo "==> Running ruff format check..."
uv run ruff format --check .

echo "==> Running pytest..."
uv run pytest -v

echo "==> All backend tests passed!"
