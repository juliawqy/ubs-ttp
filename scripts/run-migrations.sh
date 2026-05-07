#!/bin/bash
set -e
SERVICES=(api-gateway recruitment training performance ai-assistant analytics)
for svc in "${SERVICES[@]}"; do
  echo "🔄 Running migrations for $svc..."
  cd services/$svc
  alembic upgrade head
  cd ../..
done
echo "✅ All migrations complete."
