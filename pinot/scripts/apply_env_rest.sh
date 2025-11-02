#!/usr/bin/env bash
set -euo pipefail

# Apply Pinot schemas and tables using Controller REST API.
# Usage:
#   ENV=staging PINOT_CONTROLLER=https://pinot-staging.paklog.com AUTH_TOKEN=$TOKEN \
#   bash pinot/scripts/apply_env_rest.sh

ENV=${ENV:-dev}
PINOT_CONTROLLER=${PINOT_CONTROLLER:-http://localhost:9000}
AUTH_TOKEN=${AUTH_TOKEN:-}

hdr=("-H" "Content-Type: application/json")
if [[ -n "${AUTH_TOKEN}" ]]; then
  hdr+=("-H" "Authorization: Bearer ${AUTH_TOKEN}")
fi

echo "Applying schemas to ${PINOT_CONTROLLER}..."
while IFS= read -r -d '' schema; do
  echo "  -> ${schema}"
  curl -sS -X POST "${PINOT_CONTROLLER}/schemas?override=true" "${hdr[@]}" --data-binary @"${schema}" > /dev/null
done < <(find pinot/schemas -type f -name '*.schema.json' -print0 | sort -z)

echo "Applying tables (${ENV}) to ${PINOT_CONTROLLER}..."
while IFS= read -r -d '' table; do
  echo "  -> ${table}"
  curl -sS -X POST "${PINOT_CONTROLLER}/tables" "${hdr[@]}" --data-binary @"${table}" > /dev/null
done < <(find pinot/tables -type f -name "*.table.${ENV}.json" -print0 | sort -z)

echo "Done."

