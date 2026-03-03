-- Seed for manual Swagger testing of LLM endpoint
-- Usage:
--   psql "$APP_CONFIG__DB__URL" -f tests/seed_swagger_llm.sql
-- or run inside your DB client connected to project database.

BEGIN;

-- Stable IDs for manual testing
-- User:          11111111-1111-1111-1111-111111111111
-- TG user id:    100500
-- AI models:     22222222-2222-2222-2222-222222222221 .. 22222222-2222-2222-2222-222222222232
-- LLM models:    33333333-3333-3333-3333-333333333331 .. 33333333-3333-3333-3333-333333333336
-- Image models:  33333333-3333-3333-3333-333333333341 .. 33333333-3333-3333-3333-333333333342
-- Video models:  33333333-3333-3333-3333-333333333351 .. 33333333-3333-3333-3333-333333333352

-- Providers used in this seed:
-- LLM:   openai/gpt-4o-mini, openai/gpt-5.2, openai/gpt-5.1, openai/gpt-4, x-ai/grok-4, anthropic/claude-sonnet-4.5
-- Image: openai/dall-e-3, google/nano-banana-2/text-to-image
-- Video: openai/sora-2, google/veo-3

-- Clean previous seed (idempotent)
DELETE FROM ai_generations
WHERE user_id = '11111111-1111-1111-1111-111111111111'
   OR ai_model_id IN (
       '22222222-2222-2222-2222-222222222221',
       '22222222-2222-2222-2222-222222222222',
       '22222222-2222-2222-2222-222222222223',
       '22222222-2222-2222-2222-222222222224',
       '22222222-2222-2222-2222-222222222225',
       '22222222-2222-2222-2222-222222222226',
       '22222222-2222-2222-2222-222222222227',
       '22222222-2222-2222-2222-222222222228',
       '22222222-2222-2222-2222-222222222231',
       '22222222-2222-2222-2222-222222222232'
   )
   OR ai_model_id IN (
       SELECT id
       FROM ai_models
       WHERE provider_key IN (
           'openai/gpt-4o-mini',
           'openai/gpt-5.2',
           'openai/gpt-5.1',
           'openai/gpt-4',
           'x-ai/grok-4',
           'anthropic/claude-sonnet-4.5',
           'openai/dall-e-3',
           'google/nano-banana-2/text-to-image',
           'openai/sora-2',
           'google/veo-3'
       )
   );

DELETE FROM llm_configurations
WHERE user_id = '11111111-1111-1111-1111-111111111111';

DELETE FROM user_balances
WHERE user_id = '11111111-1111-1111-1111-111111111111';

DELETE FROM llm_models
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222223',
    '22222222-2222-2222-2222-222222222224',
    '22222222-2222-2222-2222-222222222225',
    '22222222-2222-2222-2222-222222222226'
);

DELETE FROM image_models
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222231',
    '22222222-2222-2222-2222-222222222232'
);

DELETE FROM video_models
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222227',
    '22222222-2222-2222-2222-222222222228'
);

DELETE FROM llm_models
WHERE ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN (
        'openai/gpt-4o-mini',
        'openai/gpt-5.2',
        'openai/gpt-5.1',
        'openai/gpt-4',
        'x-ai/grok-4',
        'anthropic/claude-sonnet-4.5'
    )
);

DELETE FROM image_models
WHERE ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN ('openai/dall-e-3', 'google/nano-banana-2/text-to-image')
);

DELETE FROM video_models
WHERE ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN ('openai/sora-2', 'google/veo-3')
);

DELETE FROM ai_models
WHERE id IN (
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222223',
    '22222222-2222-2222-2222-222222222224',
    '22222222-2222-2222-2222-222222222225',
    '22222222-2222-2222-2222-222222222226',
    '22222222-2222-2222-2222-222222222227',
    '22222222-2222-2222-2222-222222222228',
    '22222222-2222-2222-2222-222222222231',
    '22222222-2222-2222-2222-222222222232'
);

DELETE FROM ai_models
WHERE provider_key IN (
    'openai/gpt-4o-mini',
    'openai/gpt-5.2',
    'openai/gpt-5.1',
    'openai/gpt-4',
    'x-ai/grok-4',
    'anthropic/claude-sonnet-4.5',
    'openai/dall-e-3',
    'google/nano-banana-2/text-to-image',
    'openai/sora-2',
    'google/veo-3'
);

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
WHERE id = '11111111-1111-1111-1111-111111111111'
    OR telegram_id = 100500;

-- User + balance
INSERT INTO users (id, telegram_id, is_active)
VALUES ('11111111-1111-1111-1111-111111111111', 100500, TRUE);

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
INSERT INTO ai_models (
    id,
    name,
    provider_key,
    is_active,
    description,
    model_type,
    min_charge_tokens,
    free_requests_limit
)
VALUES
    (
        '22222222-2222-2222-2222-222222222221',
        'GPT-4o mini (FREE)',
        'openai/gpt-4o-mini',
        TRUE,
        'БЕСПЛАТНАЯ быстрая модель для простых задач.',
        'LLM',
        10,
        10
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'GPT-5.2',
        'openai/gpt-5.2',
        TRUE,
        'Самая продвинутая модель ChatGPT.',
        'LLM',
        10,
        10
    ),
    (
        '22222222-2222-2222-2222-222222222223',
        'GPT-5.1',
        'openai/gpt-5.1',
        TRUE,
        NULL,
        'LLM',
        45,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222224',
        'GPT-4',
        'openai/gpt-4',
        TRUE,
        'Старая надежная модель OpenAI.',
        'LLM',
        30,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222225',
        'Grok 4',
        'x-ai/grok-4',
        TRUE,
        'Модель от Илона Маска.',
        'LLM',
        10,
        10
    ),
    (
        '22222222-2222-2222-2222-222222222226',
        'Claude Sonnet 4.5',
        'anthropic/claude-sonnet-4.5',
        TRUE,
        'Отлично справляется с анализом и творчеством.',
        'LLM',
        40,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222227',
        'Sora 2',
        'openai/sora-2',
        TRUE,
        'Видео-генерация высокого качества.',
        'VIDEO',
        120,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222228',
        'Veo 3',
        'google/veo-3',
        TRUE,
        'Кинематографичная видео-генерация.',
        'VIDEO',
        150,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222231',
        'Nano-banana',
        'google/nano-banana-2/text-to-image',
        TRUE,
        'Быстрая и дешевая генерация изображений.',
        'IMAGE',
        30,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222232',
        'DALLE E',
        'openai/dall-e-3',
        TRUE,
        'Качественная генерация изображений.',
        'IMAGE',
        40,
        0
    );

-- LLM model settings + provider pricing per 1M tokens
INSERT INTO llm_models (
    id,
    ai_model_id,
    input_price_per_million_usd,
    output_price_per_million_usd,
    is_temperature_support
)
VALUES
    (
        '33333333-3333-3333-3333-333333333331',
        '22222222-2222-2222-2222-222222222221',
        0.15,
        0.60,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333332',
        '22222222-2222-2222-2222-222222222222',
        1.25,
        10.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        '22222222-2222-2222-2222-222222222223',
        0.90,
        7.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333334',
        '22222222-2222-2222-2222-222222222224',
        0.50,
        2.50,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333335',
        '22222222-2222-2222-2222-222222222225',
        1.10,
        8.50,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333336',
        '22222222-2222-2222-2222-222222222226',
        1.00,
        7.50,
        TRUE
    );

-- Image model settings
INSERT INTO image_models (
    id,
    ai_model_id
)
VALUES
    (
        '33333333-3333-3333-3333-333333333341',
        '22222222-2222-2222-2222-222222222231'
    ),
    (
        '33333333-3333-3333-3333-333333333342',
        '22222222-2222-2222-2222-222222222232'
    );

-- Video model settings
INSERT INTO video_models (
    id,
    ai_model_id
)
VALUES
    (
        '33333333-3333-3333-3333-333333333351',
        '22222222-2222-2222-2222-222222222227'
    ),
    (
        '33333333-3333-3333-3333-333333333352',
        '22222222-2222-2222-2222-222222222228'
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
-- tg_user_id:               100500
-- resolved user_id:         11111111-1111-1111-1111-111111111111
-- free llm model_id:        22222222-2222-2222-2222-222222222221
-- paid llm model_id:        22222222-2222-2222-2222-222222222222
-- video model examples:     22222222-2222-2222-2222-222222222227, 22222222-2222-2222-2222-222222222228
-- image model examples:     22222222-2222-2222-2222-222222222231, 22222222-2222-2222-2222-222222222232
