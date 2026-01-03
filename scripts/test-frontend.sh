#!/bin/bash
set -e

cd "$(dirname "$0")/../frontend"

echo "==> Installing dependencies..."
npm ci --legacy-peer-deps

echo "==> Running ESLint..."
npm run lint -- --max-warnings=-1

echo "==> Running build..."
npm run build

echo "==> All frontend tests passed!"
