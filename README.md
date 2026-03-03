# AI App (Monorepo)

В этом репозитории 2 сервиса:

- `backend/` — FastAPI API
- `bot/` — Telegram-бот

## Общий конфиг (вынесен в root)

- `./.env` — единый env для backend + bot
- `./docker-compose.yml` — общие инфраструктурные сервисы (PostgreSQL, Redis)
- `./pyproject.toml` — `uv` workspace

Скопируй шаблон:

```bash
cp .env.example .env
```

## Запуск

1) Инфраструктура:

```bash
docker compose up -d
```

2) Backend:

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

3) Bot:

```bash
cd bot
uv sync
uv run python -m src.main
```
