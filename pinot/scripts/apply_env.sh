#!/usr/bin/env bash
set -euo pipefail

# Usage: ENV=dev PINOT_CONTROLLER=http://localhost:9000 ./pinot/scripts/apply_env.sh
# Optional: AUTH_TOKEN=... for secured controllers

ENV=${ENV:-dev}
PINOT_CONTROLLER=${PINOT_CONTROLLER:-http://localhost:9000}
PINOT_ADMIN=${PINOT_ADMIN:-pinot-admin.sh}
AUTH_TOKEN=${AUTH_TOKEN:-}

echo "Applying Pinot schemas..."
find pinot/schemas -type f -name '*.schema.json' | sort | while read -r schema; do
  echo "  -> ${schema}"
  if [[ -n "$AUTH_TOKEN" ]]; then
    "$PINOT_ADMIN" AddSchema -schemaFile "$schema" -controllerUrl "$PINOT_CONTROLLER" -authToken "$AUTH_TOKEN" -exec
  else
    "$PINOT_ADMIN" AddSchema -schemaFile "$schema" -controllerUrl "$PINOT_CONTROLLER" -exec
  fi
done

echo "Applying Pinot tables for ENV=${ENV}..."
find pinot/tables -type f -name "*.table.${ENV}.json" | sort | while read -r table; do
  echo "  -> ${table}"
  if [[ -n "$AUTH_TOKEN" ]]; then
    "$PINOT_ADMIN" AddTable -tableConfigFile "$table" -controllerUrl "$PINOT_CONTROLLER" -authToken "$AUTH_TOKEN" -exec
  else
    "$PINOT_ADMIN" AddTable -tableConfigFile "$table" -controllerUrl "$PINOT_CONTROLLER" -exec
  fi
done

echo "Done."

