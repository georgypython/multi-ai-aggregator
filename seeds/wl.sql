BEGIN;

-- Add/activate whitelisted Telegram user
INSERT INTO users (
    id,
    telegram_id,
    is_active,
    is_whitelist
)
VALUES (
    '55555555-5555-5555-5555-555555550002',
    5854450847,
    TRUE,
    TRUE
)
ON CONFLICT (telegram_id) DO UPDATE SET
    is_active = TRUE,
    is_whitelist = TRUE;

-- Add/activate second whitelisted Telegram user
INSERT INTO users (
    id,
    telegram_id,
    is_active,
    is_whitelist
)
VALUES (
    '55555555-5555-5555-5555-555555550003',
    8309544627,
    TRUE,
    TRUE
)
ON CONFLICT (telegram_id) DO UPDATE SET
    is_active = TRUE,
    is_whitelist = TRUE;

-- Ensure user has a balance row (do not overwrite existing values)
INSERT INTO user_balances (
    id,
    user_id,
    available_tokens,
    hold_tokens
)
SELECT
    '55555555-5555-5555-5555-555555550102',
    u.id,
    1000,
    0
FROM users u
WHERE u.telegram_id = 5854450847
ON CONFLICT (user_id) DO NOTHING;

-- Ensure second user has a balance row (do not overwrite existing values)
INSERT INTO user_balances (
    id,
    user_id,
    available_tokens,
    hold_tokens
)
SELECT
    '55555555-5555-5555-5555-555555550103',
    u.id,
    1000,
    0
FROM users u
WHERE u.telegram_id = 8309544627
ON CONFLICT (user_id) DO NOTHING;

COMMIT;
