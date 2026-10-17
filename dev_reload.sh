#!/usr/bin/env bash
docker compose down
docker volume rm ai-aggregator-app_rabbitmq_data ai-aggregator-app_postgres_data ai-aggregator-app_minio_data 
docker compose up -d --build
sleep 5
docker exec -i app-db psql -U postgres -d postgres < seeds/base_seed.sql
docker exec -i app-db psql -U postgres -d postgres < seeds/seed_billing_products_plans.sql
docker exec -i app-db psql -U postgres -d postgres < seeds/wl.sql
