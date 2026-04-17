-- Webhook-only smoke seed for payment flow.
-- Precondition: run backend/seeds/seed_billing_products_plans.sql first.
-- This seed creates 2 test payment intents for /webhooks/lava-top/regular:
--   1) TEST-WEBHOOK-SUCCESS-001
--   2) TEST-WEBHOOK-FAILED-001

BEGIN;

-- Dedicated test users
INSERT INTO users (id, telegram_id, is_active, is_whitelist)
VALUES
    ('95555555-5555-5555-5555-555555559001', 700009001, TRUE, TRUE),
    ('95555555-5555-5555-5555-555555559002', 700009002, TRUE, TRUE)
ON CONFLICT (telegram_id) DO UPDATE SET
    is_active = TRUE,
    is_whitelist = TRUE;

-- Ensure balance rows exist
INSERT INTO user_balances (id, user_id, available_tokens, hold_tokens)
SELECT
    '95555555-5555-5555-5555-555555559101',
    u.id,
    0,
    0
FROM users u
WHERE u.telegram_id = 700009001
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_balances (id, user_id, available_tokens, hold_tokens)
SELECT
    '95555555-5555-5555-5555-555555559102',
    u.id,
    0,
    0
FROM users u
WHERE u.telegram_id = 700009002
ON CONFLICT (user_id) DO NOTHING;

-- Cleanup previous smoke data for deterministic reruns
DELETE FROM balance_transactions
WHERE user_id IN (
    '95555555-5555-5555-5555-555555559001',
    '95555555-5555-5555-5555-555555559002'
);

DELETE FROM payment_transactions
WHERE payment_intent_id IN (
    '96666666-6666-6666-6666-666666669001',
    '96666666-6666-6666-6666-666666669002'
);

DELETE FROM payment_intents
WHERE id IN (
    '96666666-6666-6666-6666-666666669001',
    '96666666-6666-6666-6666-666666669002'
);

DELETE FROM orders
WHERE id IN (
    '97777777-7777-7777-7777-777777779001',
    '97777777-7777-7777-7777-777777779002'
);

DELETE FROM subscriptions
WHERE user_id IN (
    '95555555-5555-5555-5555-555555559001',
    '95555555-5555-5555-5555-555555559002'
);

-- Order + intent for SUCCESS webhook
INSERT INTO orders (
    id,
    user_id,
    plan_id,
    payment_type,
    amount,
    currency,
    discount_amount,
    status,
    expires_at,
    paid_at,
    meta_data
)
VALUES (
    '97777777-7777-7777-7777-777777779001',
    '95555555-5555-5555-5555-555555559001',
    '30000000-0000-0000-0000-000000000001',
    'RECURRING',
    480.00,
    'RUB',
    0.00,
    'PENDING',
    NOW() + INTERVAL '1 day',
    NULL,
    '{}'::jsonb
);

INSERT INTO payment_intents (
    id,
    order_id,
    provider,
    provider_invoice_id,
    provider_contract_id,
    provider_offer_id,
    status,
    invoice_url,
    provider_data
)
VALUES (
    '96666666-6666-6666-6666-666666669001',
    '97777777-7777-7777-7777-777777779001',
    'LAVA_TOP',
    'TEST-WEBHOOK-SUCCESS-001',
    NULL,
    '41000000-0000-0000-0000-000000000001',
    'AWAITING_PAYMENT',
    'https://example.local/success',
    '{"buyer_email":"tg-700009001@users.ai"}'::jsonb
);

-- Order + intent for FAILED webhook
INSERT INTO orders (
    id,
    user_id,
    plan_id,
    payment_type,
    amount,
    currency,
    discount_amount,
    status,
    expires_at,
    paid_at,
    meta_data
)
VALUES (
    '97777777-7777-7777-7777-777777779002',
    '95555555-5555-5555-5555-555555559002',
    '30000000-0000-0000-0000-000000000002',
    'ONE_TIME',
    990.00,
    'RUB',
    0.00,
    'PENDING',
    NOW() + INTERVAL '1 day',
    NULL,
    '{}'::jsonb
);

INSERT INTO payment_intents (
    id,
    order_id,
    provider,
    provider_invoice_id,
    provider_contract_id,
    provider_offer_id,
    status,
    invoice_url,
    provider_data
)
VALUES (
    '96666666-6666-6666-6666-666666669002',
    '97777777-7777-7777-7777-777777779002',
    'LAVA_TOP',
    'TEST-WEBHOOK-FAILED-001',
    NULL,
    '43000000-0000-0000-0000-000000000002',
    'AWAITING_PAYMENT',
    'https://example.local/failed',
    '{"buyer_email":"tg-700009002@users.ai"}'::jsonb
);

COMMIT;
