SHELL := /bin/bash

# Variables
ENV ?= dev
PINOT_CONTROLLER ?= http://localhost:9000

.PHONY: help
help:
	@echo "Targets:"
	@echo "  validate-json           Validate all Pinot JSON files with jq"
	@echo "  validate-transforms     Validate transforms against sample events"
	@echo "  validate                Run all validation targets"
	@echo "  apply-dev               Apply schemas/tables to dev controller"
	@echo "  apply-staging           Apply schemas/tables to staging controller"

.PHONY: validate-json
validate-json:
	@command -v jq >/dev/null || (echo "jq is required" && exit 1)
	@echo "Validating JSON schemas and tables..."
	@find pinot/schemas pinot/tables -type f -name '*.json' -print0 | xargs -0 -I{} sh -c 'jq empty {} >/dev/null' && echo "JSON OK"

.PHONY: validate-transforms
validate-transforms:
	@echo "Validating transformConfigs with sample events..."
	@python3 pinot/tools/validate_transforms.py --table pinot/tables/order-management/dp_order_management_events_v1.table.dev.json --sample pinot/samples/order-management/order-received.cloudevent.json
	@python3 pinot/tools/validate_transforms.py --table pinot/tables/inventory/dp_inventory_stock_level_v1.table.dev.json --sample pinot/samples/inventory/stock-level-changed.cloudevent.json
	@python3 pinot/tools/validate_transforms.py --table pinot/tables/physical-tracking-service/dp_physical_tracking_events_v1.table.dev.json --sample pinot/samples/physical-tracking-service/licenseplate.moved.json
	@python3 pinot/tools/validate_transforms.py --table pinot/tables/customer-experience-hub/dp_customer_experience_hub_events_v1.table.dev.json --sample pinot/samples/customer-experience-hub/ticket-created.cloudevent.json

.PHONY: validate
validate: validate-json validate-transforms

.PHONY: apply-dev
apply-dev:
	@ENV=dev PINOT_CONTROLLER=$(PINOT_CONTROLLER) bash pinot/scripts/apply_env_rest.sh

.PHONY: apply-staging
apply-staging:
	@ENV=staging PINOT_CONTROLLER=$(PINOT_CONTROLLER) bash pinot/scripts/apply_env_rest.sh

