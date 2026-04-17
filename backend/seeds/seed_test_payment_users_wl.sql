-- Test users for payment smoke checks (invoice + webhook).
-- Safe to run multiple times.

BEGIN;

-- User #1 (whitelisted)
INSERT INTO users (
    id,
    telegram_id,
    is_active,
    is_whitelist
)
VALUES (
    '55555555-5555-5555-5555-555555559001',
    700000101,
    TRUE,
    TRUE
)
ON CONFLICT (telegram_id) DO UPDATE SET
    is_active = TRUE,
    is_whitelist = TRUE;

-- User #2 (whitelisted)
INSERT INTO users (
    id,
    telegram_id,
    is_active,
    is_whitelist
)
VALUES (
    '55555555-5555-5555-5555-555555559002',
    700000102,
    TRUE,
    TRUE
)
ON CONFLICT (telegram_id) DO UPDATE SET
    is_active = TRUE,
    is_whitelist = TRUE;

-- Ensure balance rows exist (do not overwrite existing values)
INSERT INTO user_balances (
    id,
    user_id,
    available_tokens,
    hold_tokens
)
SELECT
    '55555555-5555-5555-5555-555555559101',
    u.id,
    0,
    0
FROM users u
WHERE u.telegram_id = 700000101
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_balances (
    id,
    user_id,
    available_tokens,
    hold_tokens
)
SELECT
    '55555555-5555-5555-5555-555555559102',
    u.id,
    0,
    0
FROM users u
WHERE u.telegram_id = 700000102
ON CONFLICT (user_id) DO NOTHING;

COMMIT;
