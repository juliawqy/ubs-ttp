#!/bin/bash
set -e

echo "🔧 Setting up local dev environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required. Aborting."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 20+ is required. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.12+ is required. Aborting."; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "Terraform is optional for local dev."; }

# Copy env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "📋 Created .env from .env.example — fill in your API keys."
fi

# Pre-commit
pip install pre-commit -q
pre-commit install

# Frontend deps
cd frontend && npm install && cd ..

echo "✅ Setup complete. Run 'make dev' to start all services."
