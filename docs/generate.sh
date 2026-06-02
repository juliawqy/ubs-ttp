#!/bin/bash
# Documentation-as-code generator
# Generates HTML docs from Python docstrings using pdoc
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/docs/generated"
VENV="$REPO_ROOT/docs/.venv"
mkdir -p "$OUT"

# Create a venv for doc generation so we don't need system-wide installs
if [ ! -d "$VENV" ]; then
  echo "Creating venv for doc generation..."
  python3 -m venv "$VENV"
fi

PIP="$VENV/bin/pip"
PYTHON="$VENV/bin/python"

echo "Installing dependencies..."
$PIP install -q pdoc fastapi pydantic pydantic-settings \
  sqlalchemy httpx pdfplumber python-docx anthropic \
  boto3 pandas

echo "Generating Python module docs..."
for svc in shared recruitment training performance ai-assistant analytics; do
  echo "  - $svc"
  PYTHONPATH="$REPO_ROOT/services" \
    $PYTHON -m pdoc "$REPO_ROOT/services/$svc" \
    --output-dir "$OUT/$svc" || echo "    (skipped $svc)"
done

echo "Done. Open docs/generated/*/index.html in your browser."
