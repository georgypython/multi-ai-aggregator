# AI App Pricing Model v1 (fixed)

Date fixed: 2026-04-16
Status: accepted for implementation draft

## Scope
This file fixes the selected pricing model discussed in chat, so it can be used as the source of truth for backend and frontend implementation.

## Tariff names
- Bazovyy
- Optimalnyy
- Premium

## Prices and token grants
- Bazovyy: 480 RUB -> 290 tokens
- Optimalnyy: 990 RUB -> 620 tokens
- Premium: 1990 RUB -> 1300 tokens

## Optional Premium bonus
Premium can include an optional VPN bonus:
- Bonus type: 30 days VPN subscription
- Rule: only for the first Premium purchase of a user
- Rollout phase 1 (manual):
  - payment success notification to support
  - user can message support manually
  - support verifies "first Premium purchase" and grants bonus
- Idempotency: bonus must never be granted twice for the same user

## Calculation assumptions
- Current billing config baseline from seed:
  - rub_per_token = 1.00
  - usd_per_token = 0.010
  - provider_cost_multiplier = 1.20
- Estimated internal token cost:
  - 1 / 1.20 = 0.8333 RUB per token
- Generation count estimates are for cheapest options:
  - LLM: scenario 2k input + 1k output = 0.108 tokens per generation
  - Image: 1.08 tokens per generation
  - Video: 48 tokens per generation

## Unit economics by tariff

### Bazovyy
- Price: 480 RUB
- Tokens: 290
- Effective token price for user: 1.655 RUB/token
- Estimated token COGS: 241.7 RUB
- Estimated gross profit: 238.3 RUB
- Estimated gross margin: 49.7%

Estimated max generations (single type only):
- LLM: 2685
- Image: 268
- Video: 6

### Optimalnyy
- Price: 990 RUB
- Tokens: 620
- Effective token price for user: 1.597 RUB/token
- Estimated token COGS: 516.5 RUB
- Estimated gross profit: 473.5 RUB
- Estimated gross margin: 47.8%

Estimated max generations (single type only):
- LLM: 5740
- Image: 574
- Video: 12

### Premium
- Price: 1990 RUB
- Tokens: 1300
- Effective token price for user: 1.531 RUB/token
- Estimated token COGS: 1082.9 RUB
- Estimated gross profit: 907.1 RUB
- Estimated gross margin: 45.6%

Estimated max generations (single type only):
- LLM: 12037
- Image: 1203
- Video: 27

## Notes
- These economics do not include payment processing fees, refunds, chargebacks, support cost, or marketing CAC.
- If Premium VPN bonus is enabled, include VPN COGS as a separate line item in PnL.
