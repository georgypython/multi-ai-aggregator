-- Base seed for local/dev environment
-- Contains only common AI models and token prices.
-- No user, balance, or user-specific configurations are created.

BEGIN;

-- Stable IDs used by this seed
-- AI models:  22222222-2222-2222-2222-222222222221 .. 22222222-2222-2222-2222-222222222235
-- LLM models: 33333333-3333-3333-3333-333333333331 .. 33333333-3333-3333-3333-333333333338
-- Prices:     44444444-4444-4444-4444-444444444441 .. 44444444-4444-4444-4444-444444444443

-- Providers used in this seed:
-- LLM:   openai/gpt-4o-mini, openai/gpt-5.2, openai/gpt-5.1, openai/gpt-5.3-chat, openai/gpt-5.4, openai/gpt-4, x-ai/grok-4, anthropic/claude-sonnet-4.5
-- Image: openai/dall-e-3, openai/gpt-image-1.5/text-to-image, google/nano-banana-2/text-to-image
-- Video: openai/sora-2/text-to-video, google/veo3.1/text-to-video

-- Clean previous seed data (idempotent)
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
	'22222222-2222-2222-2222-222222222235'
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
		'x-ai/grok-4',
		'anthropic/claude-sonnet-4.5',
		'openai/dall-e-3',
		'openai/gpt-image-1.5/text-to-image',
		'google/nano-banana-2/text-to-image',
		'openai/sora-2/text-to-video',
		'google/veo3.1/text-to-video'
	)
);

DELETE FROM llm_models
WHERE ai_model_id IN (
	'22222222-2222-2222-2222-222222222221',
	'22222222-2222-2222-2222-222222222222',
	'22222222-2222-2222-2222-222222222223',
	'22222222-2222-2222-2222-222222222234',
	'22222222-2222-2222-2222-222222222235',
	'22222222-2222-2222-2222-222222222224',
	'22222222-2222-2222-2222-222222222225',
	'22222222-2222-2222-2222-222222222226'
);

DELETE FROM llm_models
WHERE ai_model_id IN (
	SELECT id
	FROM ai_models
	WHERE provider_key IN (
		'openai/gpt-4o-mini',
		'openai/gpt-5.2',
		'openai/gpt-5.1',
		'openai/gpt-5.3-chat',
		'openai/gpt-5.4',
		'openai/gpt-4',
		'x-ai/grok-4',
		'anthropic/claude-sonnet-4.5'
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
	'22222222-2222-2222-2222-222222222235'
);

DELETE FROM ai_models
WHERE provider_key IN (
	'openai/gpt-4o-mini',
	'openai/gpt-5.2',
	'openai/gpt-5.1',
	'openai/gpt-5.3-chat',
	'openai/gpt-5.4',
	'openai/gpt-4',
	'x-ai/grok-4',
	'anthropic/claude-sonnet-4.5',
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

UPDATE token_prices
SET is_active = FALSE
WHERE price_type = 'USAGE';

-- AI Models
INSERT INTO ai_models (
	id,
	name,
	provider_key,
	is_active,
	description,
	model_type,
	min_charge_tokens,
	free_requests_limit,
	images_edit_support
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
		10,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222222',
		'GPT-5.2',
		'openai/gpt-5.2',
		TRUE,
		'Самая продвинутая модель ChatGPT.',
		'LLM',
		10,
		10,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222223',
		'GPT-5.1',
		'openai/gpt-5.1',
		TRUE,
		NULL,
		'LLM',
		45,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222234',
		'GPT-5.3 Chat',
		'openai/gpt-5.3-chat',
		TRUE,
		'Новая chat-модель семейства GPT-5.',
		'LLM',
		15,
		5,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222235',
		'GPT-5.4',
		'openai/gpt-5.4',
		TRUE,
		'Новая флагманская модель GPT-5.',
		'LLM',
		20,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222224',
		'GPT-4',
		'openai/gpt-4',
		TRUE,
		'Старая надежная модель OpenAI.',
		'LLM',
		30,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222225',
		'Grok 4',
		'x-ai/grok-4',
		TRUE,
		'Модель от Илона Маска.',
		'LLM',
		10,
		10,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222226',
		'Claude Sonnet 4.5',
		'anthropic/claude-sonnet-4.5',
		TRUE,
		'Отлично справляется с анализом и творчеством.',
		'LLM',
		40,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222227',
		'Sora 2',
		'openai/sora-2/text-to-video',
		TRUE,
		'Видео-генерация высокого качества.',
		'VIDEO',
		120,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222228',
		'Veo 3.1',
		'google/veo3.1/text-to-video',
		TRUE,
		'Кинематографичная видео-генерация.',
		'VIDEO',
		150,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222231',
		'Nano-banana',
		'google/nano-banana-2/text-to-image',
		TRUE,
		'Быстрая и дешевая генерация изображений.',
		'IMAGE',
		5,
		0,
		TRUE
	),
	(
		'22222222-2222-2222-2222-222222222232',
		'DALLE E',
		'openai/dall-e-3',
		TRUE,
		'Качественная генерация изображений.',
		'IMAGE',
		5,
		0,
		FALSE
	),
	(
		'22222222-2222-2222-2222-222222222233',
		'GPT Image 1.5',
		'openai/gpt-image-1.5/text-to-image',
		TRUE,
		'Гибкая генерация изображений от OpenAI.',
		'IMAGE',
		5,
		2,
		TRUE
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
