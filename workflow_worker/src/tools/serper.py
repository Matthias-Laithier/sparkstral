"""Serper web search tool definition and HTTP call."""

import http.client
import json

from mistralai.client.models import Function, Tool

SERPER_TOOL = Tool(
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


def serper_search(query: str, api_key: str) -> str:
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
