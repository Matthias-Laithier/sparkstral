import functools
from typing import Any, Literal

import httpx
from mistralai.client import Mistral

from src.config import settings
from src.schemas import SparkstralStep
from mistralai.client.httpclient import AsyncHttpClient




class LongTimeoutAsyncClient(AsyncHttpClient):
    def __init__(self) -> None:
        self.LONG_TIMEOUT = httpx.Timeout(
            connect=10.0,
            read=180.0,
            write=30.0,
            pool=10.0,
        )
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.LONG_TIMEOUT,
        )

    def build_request(self, method, url, **kwargs):
        # Force timeout even if the SDK passes its own default.
        kwargs["timeout"] = self.LONG_TIMEOUT
        return self._client.build_request(method, url, **kwargs)

    async def send(self, request, **kwargs):
        return await self._client.send(request, **kwargs)


@functools.cache
def get_mistral_client() -> Mistral:
    return Mistral(
        api_key=settings.MISTRAL_API_KEY,
        async_client=LongTimeoutAsyncClient(),
    )


def append_sparkstral_step(
    steps: list[SparkstralStep],
    *,
    label: str,
    phase: Literal["research", "structure"],
    content: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Append a `SparkstralStep` with `id` = `len(steps) + 1` before the append."""
    next_id = len(steps) + 1
    steps.append(
        SparkstralStep(
            id=next_id,
            label=label,
            phase=phase,
            content=content,
            data=data,
        )
    )
