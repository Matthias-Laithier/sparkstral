import json
from typing import Any

import pytest
from pydantic import ValidationError

import src.tools.cached_web_search as search_tool
from src.config import Settings, settings


def _settings_kwargs(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "MISTRAL_API_KEY": "test-mistral-api-key",
        "DEPLOYMENT_NAME": "test-deployment",
        "BACKEND_BASE_URL": "http://backend:8000",
        "SERPER_API_KEY": "test-serper-api-key",
        "TAVILY_API_KEY": "test-tavily-api-key",
        "WEB_SEARCH_PROVIDER": "serper",
        "WEB_SEARCH_MODEL": "mistral-small-latest",
        "WEB_SEARCH_MAX_ROUNDS": 2,
        "COMPANY_RESOLVER_AGENT_MODEL": "mistral-medium-latest",
        "COMPANY_PROFILER_AGENT_MODEL": "mistral-medium-latest",
        "PAIN_POINT_PROFILER_AGENT_MODEL": "mistral-medium-latest",
        "GENAI_USE_CASES_MODEL": "mistral-medium-latest",
        "USE_CASE_GRADER_AGENT_MODEL": "mistral-medium-latest",
        "FINAL_REPORTER_AGENT_MODEL": "mistral-medium-latest",
        "MARKDOWN_REPORTER_AGENT_MODEL": "mistral-medium-latest",
        "GENAI_USE_CASES_LLM_TEMPERATURE": 1.0,
        "LLM_MAX_TOKENS": 2048,
        "LLM_TEMPERATURE": 0.0,
    }
    values.update(overrides)
    return values


def test_settings_requires_tavily_key_for_tavily_provider() -> None:
    with pytest.raises(ValidationError, match="TAVILY_API_KEY"):
        Settings(
            **_settings_kwargs(
                WEB_SEARCH_PROVIDER="tavily",
                TAVILY_API_KEY=None,
            )
        )


@pytest.mark.asyncio
async def test_cached_web_search_uses_tavily_advanced_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, str]] = []

    class FakeTavilyClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        def search(self, *, query: str, search_depth: str) -> dict[str, Any]:
            calls.append(
                {
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": search_depth,
                }
            )
            return {
                "query": query,
                "results": [
                    {
                        "title": "Acme source",
                        "url": "https://example.com/acme",
                        "content": "Acme result",
                        "score": 0.9,
                    }
                ],
            }

    monkeypatch.setattr(settings, "WEB_SEARCH_PROVIDER", "tavily")
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "test-tavily-api-key")
    monkeypatch.setattr(search_tool, "TavilyClient", FakeTavilyClient)

    raw = await search_tool.cached_web_search("Acme")

    assert calls == [
        {
            "api_key": "test-tavily-api-key",
            "query": "Acme",
            "search_depth": "advanced",
        }
    ]
    assert json.loads(raw) == {
        "query": "Acme",
        "results": [
            {
                "title": "Acme source",
                "url": "https://example.com/acme",
                "content": "Acme result",
                "score": 0.9,
            }
        ],
    }
