from httpx import AsyncClient


class OpenRouterService:
    def __init__(
        self,
        client: AsyncClient,
        api_key: str,
        base_url: str,
    ) -> None:
        self.client = client
        self._api_key = api_key
        self._base_url = base_url

    