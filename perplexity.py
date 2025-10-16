from typing import Any, Dict, Optional
import httpx

from .config import settings


class PerplexityClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.perplexity_api_key
        self.base_url = base_url or settings.perplexity_api_url

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def ask(self, query: str, *, model: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not set")

        payload = {
            "model": model or settings.perplexity_model,
            "messages": [
                {"role": "system", "content": "You are a helpful, factual assistant."},
                {"role": "user", "content": query},
            ],
        }

        timeout = settings.request_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(self.base_url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data

    async def search(
        self,
        query: str,
        *,
        count: int = 5,
        include_snippets: bool = True,
        search_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not set")

        payload = {
            "query": query,
            "count": int(count),
            "include_snippets": bool(include_snippets),
        }

        timeout = settings.request_timeout_seconds
        url = search_url or settings.perplexity_search_url
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data
