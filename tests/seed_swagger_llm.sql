-- Seed for manual Swagger testing of LLM endpoint
-- Usage:
--   psql "$APP_CONFIG__DB__URL" -f tests/seed_swagger_llm.sql
-- or run inside your DB client connected to project database.

BEGIN;

-- Stable IDs for manual testing
-- User:            11111111-1111-1111-1111-111111111111
-- Free AI Model:   22222222-2222-2222-2222-222222222221 (openai/gpt-4o-mini)
-- Paid AI Model:   22222222-2222-2222-2222-222222222222 (openai/gpt-5.2)
-- Free LLM Model:  33333333-3333-3333-3333-333333333331
-- Paid LLM Model:  33333333-3333-3333-3333-333333333332

-- Clean previous seed (idempotent)
DELETE FROM llm_configurations
WHERE user_id = '11111111-1111-1111-1111-111111111111';

DELETE FROM user_balances
WHERE user_id = '11111111-1111-1111-1111-111111111111';

DELETE FROM llm_models
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222'
);

DELETE FROM llm_models
WHERE ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN ('openai/gpt-4o-mini', 'openai/gpt-5.2')
);

DELETE FROM ai_models
WHERE id IN (
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222'
);

DELETE FROM ai_models
WHERE provider_key IN ('openai/gpt-4o-mini', 'openai/gpt-5.2');

DELETE FROM token_prices
WHERE id IN (
    '44444444-4444-4444-4444-444444444441',
    '44444444-4444-4444-4444-444444444442',
    '44444444-4444-4444-4444-444444444443'
);

UPDATE token_prices
SET is_active = FALSE
WHERE price_type = 'USAGE';

DELETE FROM users
WHERE id = '11111111-1111-1111-1111-111111111111';

-- User + balance
INSERT INTO users (id, is_active)
VALUES ('11111111-1111-1111-1111-111111111111', TRUE);

INSERT INTO user_balances (id, user_id, available_tokens, hold_tokens)
VALUES (
    '55555555-5555-5555-5555-555555555551',
    '11111111-1111-1111-1111-111111111111',
    500,
    0
);

-- User LLM configuration (optional but useful)
INSERT INTO llm_configurations (id, name, user_id, configuration_type, temperature, instructions)
VALUES (
    '66666666-6666-6666-6666-666666666661',
    'Swagger test config',
    '11111111-1111-1111-1111-111111111111',
    'USER',
    0.3,
    'Отвечай кратко и по делу.'
);

-- AI Models
INSERT INTO ai_models (id, name, provider_key, is_active, description)
VALUES
    (
        '22222222-2222-2222-2222-222222222221',
        'GPT-4o mini (free tier)',
        'openai/gpt-4o-mini',
        TRUE,
        'Free test model: first 3 requests are free.'
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'GPT-5.2 (paid)',
        'openai/gpt-5.2',
        TRUE,
        'Paid test model.'
    );

-- LLM model settings + provider pricing per 1M tokens
INSERT INTO llm_models (
    id,
    ai_model_id,
    input_price_per_million_usd,
    output_price_per_million_usd,
    free_requests_limit,
    min_charge_tokens,
    is_temperature_support,
    provider_price_usd,
    our_price_tokens,
    min_req_tokens
)
VALUES
    (
        '33333333-3333-3333-3333-333333333331',
        '22222222-2222-2222-2222-222222222221',
        0.15,
        0.60,
        3,
        20,
        TRUE,
        0.0,
        0,
        0
    ),
    (
        '33333333-3333-3333-3333-333333333332',
        '22222222-2222-2222-2222-222222222222',
        1.25,
        10.00,
        0,
        50,
        TRUE,
        0.0,
        0,
        0
    );

-- Token pricing (used by billing finalization)
-- IMPORTANT: exactly one active USAGE row should exist.
INSERT INTO token_prices (
    id,
    price_type,
    usd_per_token,
    rub_per_token,
    provider_cost_multiplier,
    is_active
)
VALUES
    (
        '44444444-4444-4444-4444-444444444441',
        'USAGE',
        0.010,
        1.00,
        1.20,
        TRUE
    ),
    (
        '44444444-4444-4444-4444-444444444442',
        'SUBSCRIPTION',
        0.008,
        0.80,
        NULL,
        TRUE
    ),
    (
        '44444444-4444-4444-4444-444444444443',
        'ONE_TIME',
        0.012,
        1.20,
        NULL,
        TRUE
    );

COMMIT;

-- Quick reference for Swagger tests:
-- user_id (same for all):   11111111-1111-1111-1111-111111111111
-- free model_id (3 free):   22222222-2222-2222-2222-222222222221
-- paid model_id:            22222222-2222-2222-2222-222222222222
