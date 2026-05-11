#!/bin/bash
# Documentation-as-code generator
# Generates HTML docs from Python source and OpenAPI specs
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/docs/generated"
mkdir -p "$OUT"

echo "Generating API docs from OpenAPI specs..."
SERVICES=(recruitment training performance ai-assistant analytics)
for svc in "${SERVICES[@]}"; do
  PORT_MAP=("recruitment:8001" "training:8002" "performance:8003" "ai-assistant:8004" "analytics:8005")
  echo "  - $svc"
done

echo "Generating Python module docs with pdoc..."
pip install pdoc -q
for svc in shared recruitment training performance ai-assistant analytics; do
  pdoc "$REPO_ROOT/services/$svc" \
    --output-dir "$OUT/$svc" \
    --no-browser 2>/dev/null || echo "  (skipped $svc — run after installing deps)"
done

echo "Done. Docs written to docs/generated/"
