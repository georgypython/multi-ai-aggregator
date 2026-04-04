import json
from uuid import UUID

from redis.asyncio import Redis

from src.core.config import settings


class ChatMemoryService:
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client
        self._ttl_seconds = settings.redis.chat_history_ttl_seconds
        self._history_limit = settings.redis.chat_history_limit

    @staticmethod
    def _key(user_id: UUID) -> str:
        return f"chat:ctx:{user_id}"

    async def get_chat_history(self, user_id: UUID) -> list[dict[str, str]]:
        raw_value = await self.redis.get(self._key(user_id=user_id))
        if not raw_value:
            return []

        try:
            loaded = json.loads(raw_value)
        except (TypeError, ValueError):
            return []

        if not isinstance(loaded, list):
            return []

        history: list[dict[str, str]] = []
        for item in loaded:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")
            if role in {"system", "user", "assistant"} and isinstance(content, str):
                history.append({"role": role, "content": content})

        return history[-self._history_limit :]

    async def append_user_and_assistant_messages(
        self,
        user_id: UUID,
        user_prompt: str,
        assistant_response: str,
    ) -> None:
        history = await self.get_chat_history(user_id=user_id)
        history.append({"role": "user", "content": user_prompt})
        history.append({"role": "assistant", "content": assistant_response})

        trimmed_history = history[-self._history_limit :]
        payload = json.dumps(trimmed_history, ensure_ascii=False)
        await self.redis.setex(
            self._key(user_id=user_id),
            self._ttl_seconds,
            payload,
        )
