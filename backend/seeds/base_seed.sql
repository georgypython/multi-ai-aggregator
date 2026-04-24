-- Base seed for local/dev environment (current DB schema)
-- Contains common AI models, token prices, llm/image/video profiles and all image/video prices.
-- Also seeds one whitelisted Telegram user for manual smoke checks.

BEGIN;

-- Stable IDs used by this seed
-- AI models:      22222222-2222-2222-2222-222222222221 .. 22222222-2222-2222-2222-222222222236
-- LLM profiles:   33333333-3333-3333-3333-333333333331 .. 33333333-3333-3333-3333-333333333339
-- Token prices:   44444444-4444-4444-4444-444444444441 .. 44444444-4444-4444-4444-444444444443
-- Image profiles: 66666666-6666-6666-6666-666666666231 .. 66666666-6666-6666-6666-666666666233
-- Video profiles: 77777777-7777-7777-7777-777777777227 .. 77777777-7777-7777-7777-777777777228
-- Seed user:      55555555-5555-5555-5555-555555550001 (tg: 5854450847)
-- Seed balance:   55555555-5555-5555-5555-555555550101

-- Providers covered by this seed:
-- LLM:   openai/gpt-4o-mini, openai/gpt-5.3-chat, openai/gpt-5.4, openai/gpt-4o, anthropic/claude-sonnet-4.5, anthropic/claude-sonnet-4.6, deepseek/deepseek-v4-flash, perplexity/sonar, x-ai/grok-4.20
-- Image: openai/dall-e-3, openai/gpt-image-1.5/text-to-image, google/nano-banana-2/text-to-image
-- Video: openai/sora-2/text-to-video, google/veo3.1/text-to-video

-- Idempotent cleanup
DELETE FROM ai_generations
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222223',
    '22222222-2222-2222-2222-222222222224',
    '22222222-2222-2222-2222-222222222225',
    '22222222-2222-2222-2222-222222222226',
    '22222222-2222-2222-2222-222222222227',
    '22222222-2222-2222-2222-222222222228',
    '22222222-2222-2222-2222-222222222231',
    '22222222-2222-2222-2222-222222222232',
    '22222222-2222-2222-2222-222222222233',
    '22222222-2222-2222-2222-222222222234',
    '22222222-2222-2222-2222-222222222235',
    '22222222-2222-2222-2222-222222222236'
)
OR ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN (
        'openai/gpt-4o-mini',
        'openai/gpt-5.2',
        'openai/gpt-5.1',
        'openai/gpt-5.3-chat',
        'openai/gpt-5.4',
        'openai/gpt-4',
        'openai/gpt-4o',
        'x-ai/grok-4',
        'x-ai/grok-4.20',
        'anthropic/claude-sonnet-4.5',
        'anthropic/claude-sonnet-4.6',
        'deepseek/deepseek-v4-flash',
        'perplexity/sonar',
        'openai/dall-e-3',
        'openai/gpt-image-1.5/text-to-image',
        'google/nano-banana-2/text-to-image',
        'openai/sora-2/text-to-video',
        'google/veo3.1/text-to-video'
    )
);

DELETE FROM image_prices
WHERE image_profile_id IN (
    SELECT id
    FROM image_profiles
    WHERE ai_model_id IN (
        SELECT id
        FROM ai_models
        WHERE provider_key IN (
            'openai/dall-e-3',
            'openai/gpt-image-1.5/text-to-image',
            'google/nano-banana-2/text-to-image'
        )
    )
);

DELETE FROM video_prices
WHERE video_profile_id IN (
    SELECT id
    FROM video_profiles
    WHERE ai_model_id IN (
        SELECT id
        FROM ai_models
        WHERE provider_key IN (
            'openai/sora-2/text-to-video',
            'google/veo3.1/text-to-video'
        )
    )
);

DELETE FROM image_profiles
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222231',
    '22222222-2222-2222-2222-222222222232',
    '22222222-2222-2222-2222-222222222233'
)
OR ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN (
        'openai/dall-e-3',
        'openai/gpt-image-1.5/text-to-image',
        'google/nano-banana-2/text-to-image'
    )
);

DELETE FROM video_profiles
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222227',
    '22222222-2222-2222-2222-222222222228'
)
OR ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN (
        'openai/sora-2/text-to-video',
        'google/veo3.1/text-to-video'
    )
);

DELETE FROM llm_profiles
WHERE ai_model_id IN (
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222',
    '22222222-2222-2222-2222-222222222223',
    '22222222-2222-2222-2222-222222222224',
    '22222222-2222-2222-2222-222222222225',
    '22222222-2222-2222-2222-222222222226',
    '22222222-2222-2222-2222-222222222234',
    '22222222-2222-2222-2222-222222222235',
    '22222222-2222-2222-2222-222222222236'
)
OR ai_model_id IN (
    SELECT id
    FROM ai_models
    WHERE provider_key IN (
        'openai/gpt-4o-mini',
        'openai/gpt-5.2',
        'openai/gpt-5.1',
        'openai/gpt-5.3-chat',
        'openai/gpt-5.4',
        'openai/gpt-4',
        'openai/gpt-4o',
        'x-ai/grok-4',
        'x-ai/grok-4.20',
        'anthropic/claude-sonnet-4.5',
        'anthropic/claude-sonnet-4.6',
        'deepseek/deepseek-v4-flash',
        'perplexity/sonar'
    )
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
    '22222222-2222-2222-2222-222222222232',
    '22222222-2222-2222-2222-222222222233',
    '22222222-2222-2222-2222-222222222234',
    '22222222-2222-2222-2222-222222222235',
    '22222222-2222-2222-2222-222222222236'
);

DELETE FROM ai_models
WHERE provider_key IN (
    'openai/gpt-4o-mini',
    'openai/gpt-5.2',
    'openai/gpt-5.1',
    'openai/gpt-5.3-chat',
    'openai/gpt-5.4',
    'openai/gpt-4',
    'openai/gpt-4o',
    'x-ai/grok-4',
    'x-ai/grok-4.20',
    'anthropic/claude-sonnet-4.5',
    'anthropic/claude-sonnet-4.6',
    'deepseek/deepseek-v4-flash',
    'perplexity/sonar',
    'openai/dall-e-3',
    'openai/gpt-image-1.5/text-to-image',
    'google/nano-banana-2/text-to-image',
    'openai/sora-2/text-to-video',
    'google/veo3.1/text-to-video'
);

DELETE FROM token_prices
WHERE id IN (
    '44444444-4444-4444-4444-444444444441',
    '44444444-4444-4444-4444-444444444442',
    '44444444-4444-4444-4444-444444444443'
);

-- Token prices used by billing
INSERT INTO token_prices (
    id,
    usd_per_token,
    rub_per_token,
    provider_cost_multiplier,
    is_active
)
VALUES
    (
        '44444444-4444-4444-4444-444444444441',
        0.010,
        1.00,
        1.20,
        TRUE
    ),
    (
        '44444444-4444-4444-4444-444444444442',
        0.008,
        0.80,
        NULL,
        TRUE
    ),
    (
        '44444444-4444-4444-4444-444444444443',
        0.012,
        1.20,
        NULL,
        TRUE
    );

-- AI Models (current schema includes token_price_id)
INSERT INTO ai_models (
    id,
    name,
    provider_key,
    is_active,
    description,
    model_type,
    token_price_id,
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
        '44444444-4444-4444-4444-444444444441',
        10,
        10
    ),
    (
        '22222222-2222-2222-2222-222222222234',
        'GPT-5.3 Chat',
        'openai/gpt-5.3-chat',
        TRUE,
        'Опитмальная модель для большинства задач',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        15,
        5
    ),
    (
        '22222222-2222-2222-2222-222222222235',
        'GPT-5.4',
        'openai/gpt-5.4',
        TRUE,
        'Самая последняя и сильная модель OpenAI',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        20,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222223',
        'GPT-4o',
        'openai/gpt-4o',
        TRUE,
        'Самая известная нейросеть OpenAI',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        15,
        5
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'DeepSeek V4 Flash',
        'deepseek/deepseek-v4-flash',
        TRUE,
        'Топовая китайская нейронка',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        10,
        5
    ),
    (
        '22222222-2222-2222-2222-222222222224',
        'Claude Sonnet 4.6',
        'anthropic/claude-sonnet-4.6',
        TRUE,
        'Универсальная модель от Antropic',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        40,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222225',
        'Perplexity Sonar',
        'perplexity/sonar',
        TRUE,
        'Топовая нейронка для поиска',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        15,
        3
    ),
    (
        '22222222-2222-2222-2222-222222222236',
        'Grok 4.20',
        'x-ai/grok-4.20',
        TRUE,
        'Самая последняя модель от Илона Маска',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        25,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222226',
        'Claude Sonnet 4.5',
        'anthropic/claude-sonnet-4.5',
        TRUE,
        'Отлично справляется с анализом и творчеством.',
        'LLM',
        '44444444-4444-4444-4444-444444444441',
        40,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222227',
        'Sora 2',
        'openai/sora-2/text-to-video',
        TRUE,
        'Видео-генерация высокого качества.',
        'VIDEO',
        '44444444-4444-4444-4444-444444444441',
        120,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222228',
        'Veo 3.1',
        'google/veo3.1/text-to-video',
        TRUE,
        'Кинематографичная видео-генерация.',
        'VIDEO',
        '44444444-4444-4444-4444-444444444441',
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
        '44444444-4444-4444-4444-444444444441',
        5,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222232',
        'DALLE E',
        'openai/dall-e-3',
        TRUE,
        'Качественная генерация изображений.',
        'IMAGE',
        '44444444-4444-4444-4444-444444444441',
        5,
        0
    ),
    (
        '22222222-2222-2222-2222-222222222233',
        'GPT Image 1.5',
        'openai/gpt-image-1.5/text-to-image',
        TRUE,
        'Гибкая генерация изображений от OpenAI.',
        'IMAGE',
        '44444444-4444-4444-4444-444444444441',
        5,
        2
    );

-- LLM profiles + provider pricing per 1M tokens
INSERT INTO llm_profiles (
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
        '33333333-3333-3333-3333-333333333337',
        '22222222-2222-2222-2222-222222222234',
        1.50,
        12.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333338',
        '22222222-2222-2222-2222-222222222235',
        2.00,
        16.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        '22222222-2222-2222-2222-222222222223',
        2.50,
        10.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333332',
        '22222222-2222-2222-2222-222222222222',
        0.27,
        1.10,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333334',
        '22222222-2222-2222-2222-222222222224',
        3.00,
        15.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333335',
        '22222222-2222-2222-2222-222222222225',
        1.00,
        1.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333339',
        '22222222-2222-2222-2222-222222222236',
        3.00,
        15.00,
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333336',
        '22222222-2222-2222-2222-222222222226',
        1.00,
        7.50,
        TRUE
    );

-- Image profiles
INSERT INTO image_profiles (
    id,
    ai_model_id,
    provider,
    image_edit_model_name,
    is_active
)
VALUES
    (
        '66666666-6666-6666-6666-666666666232',
        '22222222-2222-2222-2222-222222222232',
        'OPENAI',
        NULL,
        TRUE
    ),
    (
        '66666666-6666-6666-6666-666666666233',
        '22222222-2222-2222-2222-222222222233',
        'OPENAI',
        'openai/gpt-image-1.5/edit',
        TRUE
    ),
    (
        '66666666-6666-6666-6666-666666666231',
        '22222222-2222-2222-2222-222222222231',
        'GOOGLE',
        'google/nano-banana-2/edit',
        TRUE
    );

-- Video profiles
INSERT INTO video_profiles (
    id,
    ai_model_id,
    provider,
    image_edit_model_name,
    is_active
)
VALUES
    (
        '77777777-7777-7777-7777-777777777227',
        '22222222-2222-2222-2222-222222222227',
        'OPENAI',
        NULL,
        TRUE
    ),
    (
        '77777777-7777-7777-7777-777777777228',
        '22222222-2222-2222-2222-222222222228',
        'GOOGLE',
        NULL,
        TRUE
    );

-- Image prices (identical to backend/src/core/utils/image_configs.py)
INSERT INTO image_prices (
    id,
    image_profile_id,
    quality,
    size,
    provider_cost
)
VALUES
    -- openai/dall-e-3
    ('88888888-8888-8888-8888-000000000001', '66666666-6666-6666-6666-666666666232', 'standard', '1024*1024', 0.040),
    ('88888888-8888-8888-8888-000000000002', '66666666-6666-6666-6666-666666666232', 'standard', '1024*1792', 0.080),
    ('88888888-8888-8888-8888-000000000003', '66666666-6666-6666-6666-666666666232', 'standard', '1792*1024', 0.080),
    ('88888888-8888-8888-8888-000000000004', '66666666-6666-6666-6666-666666666232', 'hd', '1024*1024', 0.080),
    ('88888888-8888-8888-8888-000000000005', '66666666-6666-6666-6666-666666666232', 'hd', '1024*1792', 0.120),
    ('88888888-8888-8888-8888-000000000006', '66666666-6666-6666-6666-666666666232', 'hd', '1792*1024', 0.120),

    -- openai/gpt-image-1.5/text-to-image
    ('88888888-8888-8888-8888-000000000007', '66666666-6666-6666-6666-666666666233', 'low', '1024*1024', 0.009),
    ('88888888-8888-8888-8888-000000000008', '66666666-6666-6666-6666-666666666233', 'low', '1024*1536', 0.013),
    ('88888888-8888-8888-8888-000000000009', '66666666-6666-6666-6666-666666666233', 'low', '1536*1024', 0.013),
    ('88888888-8888-8888-8888-000000000010', '66666666-6666-6666-6666-666666666233', 'medium', '1024*1024', 0.034),
    ('88888888-8888-8888-8888-000000000011', '66666666-6666-6666-6666-666666666233', 'medium', '1024*1536', 0.051),
    ('88888888-8888-8888-8888-000000000012', '66666666-6666-6666-6666-666666666233', 'medium', '1536*1024', 0.051),
    ('88888888-8888-8888-8888-000000000013', '66666666-6666-6666-6666-666666666233', 'high', '1024*1024', 0.133),
    ('88888888-8888-8888-8888-000000000014', '66666666-6666-6666-6666-666666666233', 'high', '1024*1536', 0.200),
    ('88888888-8888-8888-8888-000000000015', '66666666-6666-6666-6666-666666666233', 'high', '1536*1024', 0.200),

    -- google/nano-banana-2/text-to-image
    ('88888888-8888-8888-8888-000000000016', '66666666-6666-6666-6666-666666666231', '1k', '1:1', 0.070),
    ('88888888-8888-8888-8888-000000000017', '66666666-6666-6666-6666-666666666231', '1k', '9:16', 0.070),
    ('88888888-8888-8888-8888-000000000018', '66666666-6666-6666-6666-666666666231', '1k', '16:9', 0.070),
    ('88888888-8888-8888-8888-000000000019', '66666666-6666-6666-6666-666666666231', '2k', '1:1', 0.105),
    ('88888888-8888-8888-8888-000000000020', '66666666-6666-6666-6666-666666666231', '2k', '9:16', 0.105),
    ('88888888-8888-8888-8888-000000000021', '66666666-6666-6666-6666-666666666231', '2k', '16:9', 0.105),
    ('88888888-8888-8888-8888-000000000022', '66666666-6666-6666-6666-666666666231', '4k', '1:1', 0.140),
    ('88888888-8888-8888-8888-000000000023', '66666666-6666-6666-6666-666666666231', '4k', '9:16', 0.140),
    ('88888888-8888-8888-8888-000000000024', '66666666-6666-6666-6666-666666666231', '4k', '16:9', 0.140);

-- Video prices (current profile pricing data)
INSERT INTO video_prices (
    id,
    video_profile_id,
    duration_seconds,
    provider_cost
)
VALUES
    -- openai/sora-2/text-to-video
    ('99999999-9999-9999-9999-000000000001', '77777777-7777-7777-7777-777777777227', 4, 0.40),
    ('99999999-9999-9999-9999-000000000003', '77777777-7777-7777-7777-777777777227', 8, 0.80),
    ('99999999-9999-9999-9999-000000000005', '77777777-7777-7777-7777-777777777227', 12, 1.20),

    -- google/veo3.1/text-to-video
    ('99999999-9999-9999-9999-000000000007', '77777777-7777-7777-7777-777777777228', 4, 1.60),
    ('99999999-9999-9999-9999-000000000009', '77777777-7777-7777-7777-777777777228', 6, 2.40),
    ('99999999-9999-9999-9999-000000000011', '77777777-7777-7777-7777-777777777228', 8, 3.20);

-- Whitelisted Telegram user for local/dev smoke checks
INSERT INTO users (
    id,
    telegram_id,
    is_active,
    is_whitelist
)
VALUES (
    '55555555-5555-5555-5555-555555550001',
    5854450847,
    TRUE,
    TRUE
)
ON CONFLICT (telegram_id) DO UPDATE SET
    is_active = EXCLUDED.is_active,
    is_whitelist = EXCLUDED.is_whitelist;

INSERT INTO user_balances (
    id,
    user_id,
    available_tokens,
    hold_tokens
)
VALUES (
    '55555555-5555-5555-5555-555555550101',
    (SELECT id FROM users WHERE telegram_id = 5854450847),
    1000,
    0
)
ON CONFLICT (user_id) DO UPDATE SET
    available_tokens = EXCLUDED.available_tokens,
    hold_tokens = EXCLUDED.hold_tokens;

COMMIT;
