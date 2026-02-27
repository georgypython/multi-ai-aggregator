import json
from uuid import UUID

from redis.asyncio import Redis

from src.core.config import settings


class ChatMemoryRepository:
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client
        self._ttl_seconds = settings.redis.chat_history_ttl_seconds
        self._history_limit = settings.redis.chat_history_limit

    @staticmethod
    def _key(user_id: UUID, chat_id: str) -> str:
        return f"chat:ctx:{user_id}:{chat_id}"
