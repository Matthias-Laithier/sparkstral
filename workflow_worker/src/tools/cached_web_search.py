"""Mistral `cached_web_search` tool: backend exact-query cache + Serper on miss."""

import json
import logging

import httpx
from mistralai.client.models import Function, Tool

from src.config import settings

logger = logging.getLogger(__name__)

CACHED_WEB_SEARCH_TOOL = Tool(
    type="function",
    function=Function(
        name="cached_web_search",
        description=(
            "Search the web for current information. Results for identical queries"
            " may be served from cache. Returns a JSON snippet with organic results"
            " (titles, snippets, and links)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                }
            },
            "required": ["query"],
        },
    ),
)


async def _serper_search(client: httpx.AsyncClient, query: str) -> str:
    response = await client.post(
        "https://google.serper.dev/search",
        content=json.dumps({"q": query}),
        headers={
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    return response.text


async def cached_web_search(query: str) -> str:
    """Look up the exact query in the backend cache; on miss, Serper + store."""
    if not query.strip():
        return "{}"
    base = settings.BACKEND_BASE_URL.rstrip("/")
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(
                f"{base}/api/web-search-cache/lookup",
                json={"query": query},
            )
            r.raise_for_status()
            data = r.json()
            if data.get("found") and isinstance(data.get("result"), str):
                return str(data["result"])
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            logger.warning("web search cache lookup failed, using Serper: %s", exc)

        raw = await _serper_search(client, query)
        try:
            s = await client.post(
                f"{base}/api/web-search-cache",
                json={"query": query, "result": raw},
            )
            s.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("web search cache store failed: %s", exc)
        return raw
