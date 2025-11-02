Pinot Data Products

Structure
- `schemas/<service>/<product>.schema.json` — Pinot schema definitions
- `tables/<service>/<product>.table.<env>.json` — Pinot realtime table configs per env (`dev`, `staging`)
- `data-products/<service>/<product>.yaml` — Data product metadata for cataloging (DataHub)

Apply (example)
1) Set env vars for staging if using SASL/SCRAM:
   - `export KAFKA_SASL_USERNAME=...`
   - `export KAFKA_SASL_PASSWORD=...`

2) Apply all schemas and tables for an environment:
   - Dev: `ENV=dev PINOT_CONTROLLER=http://localhost:9000 ./pinot/scripts/apply_env.sh`
   - Staging: `ENV=staging PINOT_CONTROLLER=https://pinot-staging.paklog.com ./pinot/scripts/apply_env.sh`
   - With auth: prefix `AUTH_TOKEN=...` or set `PINOT_ADMIN=/path/to/pinot-admin.sh` if not on PATH.

Alternative (no pinot-admin):
- REST: `ENV=staging PINOT_CONTROLLER=https://pinot-staging.paklog.com AUTH_TOKEN=... bash pinot/scripts/apply_env_rest.sh`

3) Verify in Pinot Controller UI and query via Superset.

Notes
- All tables use Kafka LLC with JSON decoder and CloudEvents envelope transforms.
- Adjust `stream.kafka.broker.list` for your environment and security.
- Extend schemas with domain keys as you stabilize payloads.

Transform validation
- Tool: `pinot/tools/validate_transforms.py`
- Validate a table’s transforms against a sample JSON event:
  - Order Management: `python3 pinot/tools/validate_transforms.py --table pinot/tables/order-management/dp_order_management_events_v1.table.dev.json --sample pinot/samples/order-management/order-received.cloudevent.json`
  - Inventory: `python3 pinot/tools/validate_transforms.py --table pinot/tables/inventory/dp_inventory_stock_level_v1.table.dev.json --sample pinot/samples/inventory/stock-level-changed.cloudevent.json`
  - Physical Tracking: `python3 pinot/tools/validate_transforms.py --table pinot/tables/physical-tracking-service/dp_physical_tracking_events_v1.table.dev.json --sample pinot/samples/physical-tracking-service/licenseplate.moved.json`

Makefile helpers
- Validate everything: `make -C pinot validate`
- Apply to dev: `make -C pinot apply-dev PINOT_CONTROLLER=http://localhost:9000`
- Apply to staging: `make -C pinot apply-staging PINOT_CONTROLLER=https://pinot-staging.paklog.com`

CI/CD (GitHub Actions)
- Workflow: `.github/workflows/pinot-deploy.yml`
- Triggers: push tag `pinot-staging-*` (deploys to staging) or manual dispatch (choose dev/staging)
- Configure these secrets in the repo:
  - `PINOT_CONTROLLER_URL_STAGING`, `PINOT_AUTH_TOKEN_STAGING`
  - (optional) `PINOT_CONTROLLER_URL_DEV`, `PINOT_AUTH_TOKEN_DEV`
