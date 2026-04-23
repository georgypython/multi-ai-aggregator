import httpx


class BaseBackendService:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._base_headers = {"X-API-Key": api_key}
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()
