DataHub Ingestion

Recipes
- Dev:
  - Kafka: datahub/recipes/dev/kafka.yml
  - Pinot: datahub/recipes/dev/pinot.yml
- Staging:
  - Kafka: datahub/recipes/staging/kafka.yml
  - Pinot: datahub/recipes/staging/pinot.yml

Environment variables
- Dev:
  - `DATAHUB_GMS_DEV` (e.g., https://datahub-dev.paklog.com)
  - `DATAHUB_TOKEN_DEV` (personal access token)
  - `KAFKA_BOOTSTRAP_DEV` (e.g., kafka-dev.paklog.com:9092)
  - `SCHEMA_REGISTRY_DEV` (e.g., https://schema-registry-dev.paklog.com)
  - `PINOT_BROKER_URL_DEV` (e.g., pinot-broker-dev.paklog.com:8099)
- Staging:
  - `DATAHUB_GMS_STAGING`
  - `DATAHUB_TOKEN_STAGING`
  - `KAFKA_BOOTSTRAP_STAGING`
  - `SCHEMA_REGISTRY_STAGING`
  - `PINOT_BROKER_URL_STAGING`

Run locally
- Install CLI: `pip install 'acryl-datahub>=0.12.3'`
- Dev: `env $(cat .env.dev | xargs) datahub ingest -c datahub/recipes/dev/kafka.yml && datahub ingest -c datahub/recipes/dev/pinot.yml`
- Staging: set the STAGING envs and run the corresponding recipes.

CI/CD
- Workflow: .github/workflows/pinot-deploy.yml
- After Pinot deploy, it ingests Kafka and Pinot metadata to DataHub for the selected environment.

