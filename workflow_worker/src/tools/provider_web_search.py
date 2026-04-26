"""Mistral `web_search` tool: Serper or Tavily, no backend cache."""

import asyncio
import json
from typing import Any, cast

import httpx
from mistralai.client.models import Function, Tool
from tavily import TavilyClient

from src.config import settings

WEB_SEARCH_TOOL = Tool(
    type="function",
    function=Function(
        name="web_search",
        description=(
            "Search the web for current information. Returns a JSON snippet with"
            " organic results (titles, snippets, and links)."
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
    api_key = settings.SERPER_API_KEY
    if api_key is None:
        raise RuntimeError("SERPER_API_KEY is required for Serper web search")

    response = await client.post(
        "https://google.serper.dev/search",
        content=json.dumps({"q": query}),
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    return response.text


async def _tavily_search(query: str) -> str:
    api_key = settings.TAVILY_API_KEY
    if api_key is None:
        raise RuntimeError("TAVILY_API_KEY is required for Tavily web search")

    def search() -> dict[str, Any]:
        client = TavilyClient(api_key)
        return cast(
            dict[str, Any],
            client.search(query=query, search_depth="basic"),
        )

    return json.dumps(await asyncio.to_thread(search))


async def web_search(query: str) -> str:
    """Search with the configured external provider (raw API, no cache)."""
    if not query.strip():
        return "{}"
    if settings.WEB_SEARCH_PROVIDER == "tavily":
        return await _tavily_search(query)
    if settings.WEB_SEARCH_PROVIDER == "serper":
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await _serper_search(client, query)
    raise RuntimeError(
        "web_search tool is only used for serper/tavily; mistralai uses built-in search"
    )
