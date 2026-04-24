"""Mistral `cached_web_search` tool: backend exact-query cache + Serper on miss."""

import asyncio
import http.client
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


def _serper_search(query: str, api_key: str) -> str:
    """Call Serper and return the raw JSON response as a string."""
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    return res.read().decode("utf-8")


async def cached_web_search(query: str) -> str:
    """Look up the exact query in the backend cache; on miss, Serper + store."""
    if not query.strip():
        return "{}"
    base = settings.BACKEND_BASE_URL.rstrip("/")
    timeout = httpx.Timeout(120.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{base}/api/web-search-cache/lookup",
                json={"query": query},
            )
            r.raise_for_status()
            data = r.json()
            if data.get("found") and isinstance(data.get("result"), str):
                return str(data["result"])
            raw = await asyncio.to_thread(
                _serper_search, query, settings.SERPER_API_KEY
            )
            try:
                s = await client.post(
                    f"{base}/api/web-search-cache",
                    json={"query": query, "result": raw},
                )
                s.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("web search cache store failed: %s", exc)
            return raw
    except (httpx.HTTPError, httpx.RequestError, KeyError, TypeError) as exc:
        logger.warning("web search cache unavailable, using Serper: %s", exc)
    return await asyncio.to_thread(_serper_search, query, settings.SERPER_API_KEY)
