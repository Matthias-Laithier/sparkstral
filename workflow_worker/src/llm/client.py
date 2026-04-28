import functools

import httpx
from mistralai.client import Mistral

from src.core.config import settings


@functools.cache
def get_mistral_client() -> Mistral:
    return Mistral(
        api_key=settings.MISTRAL_API_KEY,
        async_client=httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(
                connect=10.0,
                read=180.0,
                write=30.0,
                pool=10.0,
            ),
        ),
        timeout_ms=180_000,
    )
