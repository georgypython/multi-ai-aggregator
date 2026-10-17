-- Seed billing products and monthly plans.
-- Run after migration 330f7a84a903 is applied.

BEGIN;

-- Providers config
INSERT INTO payment_provider_configs (id, code, display_name, enabled)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'LAVA_TOP', 'LavaTop', TRUE)
ON CONFLICT (code) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    enabled = EXCLUDED.enabled;

-- Provider methods
INSERT INTO payment_provider_methods (
    id,
    provider_id,
    method_code,
    enabled,
    is_soon,
    sort_order
)
VALUES
    (
        '10000000-0000-0000-0000-000000000011',
        '10000000-0000-0000-0000-000000000001',
        'CARD_RU',
        TRUE,
        FALSE,
        10
    ),
    (
        '10000000-0000-0000-0000-000000000012',
        '10000000-0000-0000-0000-000000000001',
        'SBP',
        TRUE,
        FALSE,
        20
    ),
    (
        '10000000-0000-0000-0000-000000000013',
        '10000000-0000-0000-0000-000000000001',
        'CARD_INTERNATIONAL',
        TRUE,
        FALSE,
        30
    ),
    (
        '10000000-0000-0000-0000-000000000014',
        '10000000-0000-0000-0000-000000000001',
        'PAYPAL',
        TRUE,
        FALSE,
        40
    )
ON CONFLICT (provider_id, method_code) DO UPDATE SET
    enabled = EXCLUDED.enabled,
    is_soon = EXCLUDED.is_soon,
    sort_order = EXCLUDED.sort_order;

-- Products (tariffs)
INSERT INTO products (id, code, name, description, is_active)
VALUES
    (
        '20000000-0000-0000-0000-000000000001',
        'BAZOVYY',
        'Базовый',
        'Стартовый тариф для комфортного начала',
        TRUE
    ),
    (
        '20000000-0000-0000-0000-000000000002',
        'OPTIMALNYY',
        'Оптимальный',
        'Сбалансированный тариф для регулярного использования',
        TRUE
    ),
    (
        '20000000-0000-0000-0000-000000000003',
        'PREMIUM',
        'Премиум',
        'Максимальный пакет для активного генератора',
        TRUE
    )
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- Plans (from docs/pricing-model-v1.md)
-- Note: lavatop_* IDs below are test placeholders for local/staging smoke runs.
INSERT INTO plans (
    id,
    product_id,
    billing_interval,
    duration_days,
    price_rub,
    tokens_amount,
    lavatop_recurring_offer_id,
    lavatop_recurring_product_id,
    lavatop_one_time_offer_id,
    lavatop_one_time_product_id,
    available_payment_methods,
    is_vpn_bonus_enabled,
    display_name,
    description,
    is_active,
    llm_max_limit,
    image_max_limit,
    video_max_limit
)
VALUES
    (
        '30000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001',
        'MONTHLY',
        30,
        480.00,
        290.000000,
        '41000000-0000-0000-0000-000000000001',
        '42000000-0000-0000-0000-000000000001',
        '43000000-0000-0000-0000-000000000001',
        '44000000-0000-0000-0000-000000000001',
        '["CARD_RU", "SBP", "CARD_INTERNATIONAL"]'::jsonb,
        FALSE,
        'Базовый',
        '480 ₽ / 290 токенов / 30 дней',
        TRUE,
        2685,
        268,
        6
    ),
    (
        '30000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000002',
        'MONTHLY',
        30,
        990.00,
        620.000000,
        '41000000-0000-0000-0000-000000000002',
        '42000000-0000-0000-0000-000000000002',
        '43000000-0000-0000-0000-000000000002',
        '44000000-0000-0000-0000-000000000002',
        '["CARD_RU", "SBP", "CARD_INTERNATIONAL"]'::jsonb,
        FALSE,
        'Оптимальный',
        '990 ₽ / 620 токенов / 30 дней',
        TRUE,
        5740,
        574,
        12
    ),
    (
        '30000000-0000-0000-0000-000000000003',
        '20000000-0000-0000-0000-000000000003',
        'MONTHLY',
        30,
        1990.00,
        1300.000000,
        '41000000-0000-0000-0000-000000000003',
        '42000000-0000-0000-0000-000000000003',
        '43000000-0000-0000-0000-000000000003',
        '44000000-0000-0000-0000-000000000003',
        '["CARD_RU", "SBP", "CARD_INTERNATIONAL"]'::jsonb,
        TRUE,
        'Премиум',
        '1990 ₽ / 1300 токенов / 30 дней',
        TRUE,
        12037,
        1203,
        27
    )
ON CONFLICT (id) DO UPDATE SET
    billing_interval = EXCLUDED.billing_interval,
    duration_days = EXCLUDED.duration_days,
    price_rub = EXCLUDED.price_rub,
    tokens_amount = EXCLUDED.tokens_amount,
    lavatop_recurring_offer_id = EXCLUDED.lavatop_recurring_offer_id,
    lavatop_recurring_product_id = EXCLUDED.lavatop_recurring_product_id,
    lavatop_one_time_offer_id = EXCLUDED.lavatop_one_time_offer_id,
    lavatop_one_time_product_id = EXCLUDED.lavatop_one_time_product_id,
    available_payment_methods = EXCLUDED.available_payment_methods,
    is_vpn_bonus_enabled = EXCLUDED.is_vpn_bonus_enabled,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    llm_max_limit = EXCLUDED.llm_max_limit,
    image_max_limit = EXCLUDED.image_max_limit,
    video_max_limit = EXCLUDED.video_max_limit;

COMMIT;
