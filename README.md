# Mult-ai-aggregator

An AI models aggregator for **text, image, and video generation**, with configurable models, pricing, and subscription plans.

The project includes a FastAPI backend, an Aiogram Telegram bot, and a lightweight frontend designed as a Telegram Mini App for browsing plans and purchasing subscriptions.

## Stack

- **Backend:** FastAPI
- **Telegram Bot:** Aiogram
- **Frontend:** Mini App for the main shop
- **Database:** PostgreSQL
- **Cache:** Redis
- **Message Broker:** RabbitMQ
- **Background Tasks:** TaskIQ
- **Object Storage:** MinIO (S3-compatible)
- **Infrastructure:** Docker Compose

Models, pricing, and billing plans are configured through SQL tables, with a schema designed to support multiple AI model types.

## Quick Start

### Requirements

- Docker
- Docker Compose
- Git

### 1. Configure environment

Clone the repository and enter the project directory:

```bash
git clone git@github.com:georgypython/multi-ai-aggregator.git
cd multi-ai-aggregator 
```

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` if needed. For Telegram bot integration, obtain a bot token from [@BotFather](https://t.me/BotFather) and configure the corresponding environment variable.

### 2. Start the application

Run the development reload script:

```bash
./dev_reload.sh
```

The script rebuilds and starts the Docker Compose services, resets the project's database and storage volumes, and imports the initial test SQL seeds.

**Warning:** `dev_reload.sh` deletes the project's RabbitMQ, PostgreSQL, and MinIO volumes. Any data stored in those volumes will be lost.

### 3. Access the application

Once the containers have started, the application services should be running. Check `docker-compose.yml` and `.env` for configured ports and endpoints.

## Project Include

- **Backend API** — FastAPI application
- **Telegram Bot** — Aiogram-based bot for interact with AI models
- **Frontend** — Mini App for browsing plans and purchasing subscriptions
- **Workers** — TaskIQ background task processing
- **Infrastructure** — PostgreSQL, Redis, RabbitMQ, and MinIO, configured through Docker Compose
