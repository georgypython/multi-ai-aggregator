# AI App Bot

Telegram-бот, который работает с backend API из соседнего каталога `../backend`.

## Setup

```bash
uv sync
cd ..
cp .env.example .env
cd bot
```

Заполни переменные в `../.env`:

- `BOT__CONFIG__TG__BOT_TOKEN`
- `BOT__CONFIG__AI__API_KEY`
- `BOT__CONFIG__AI__AI_API_URL` (по умолчанию `http://localhost:8000`)

## Run

```bash
uv run python -m src.main
```

Bot читает env из общего файла `../.env` (и fallback на `./.env`).

## Smoke check

```bash
uv run python -m compileall src
```
