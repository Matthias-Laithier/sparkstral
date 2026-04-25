import json
from datetime import date
from typing import Any, cast

from mistralai.client.models import AssistantMessage, ToolMessage
from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import web_search_system_prompt
from src.tools.cached_web_search import CACHED_WEB_SEARCH_TOOL, cached_web_search


class WebSearchInput(BaseModel):
    prompt: str


class WebSearchOutput(BaseModel):
    text: str


class WebSearchAgent(BaseAgent[WebSearchInput, WebSearchOutput]):
    name = "web-search"

    async def run(self, params: WebSearchInput) -> WebSearchOutput:
        messages: list[Any] = [
            {"role": "system", "content": web_search_system_prompt(date.today())},
            {"role": "user", "content": params.prompt},
        ]

        for _ in range(settings.WEB_SEARCH_MAX_ROUNDS):
            response = await self.client.chat.complete_async(
                model=settings.WEB_SEARCH_MODEL,
                messages=messages,
                tools=[cast(Any, CACHED_WEB_SEARCH_TOOL)],
                tool_choice="auto",
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
            )
            if not response.choices:
                break

            msg = response.choices[0].message
            if msg is None:
                break

            messages.append(msg)

            if not msg.tool_calls:
                text = _text(msg).strip()
                if not text:
                    raise RuntimeError("web search returned an empty assistant message")
                return WebSearchOutput(text=text)

            for tc in msg.tool_calls:
                if tc.function.name == "cached_web_search":
                    args = json.loads(cast(str, tc.function.arguments))
                    result = await cached_web_search(args.get("query", ""))
                else:
                    result = f"Unknown tool: {tc.function.name}"

                messages.append(
                    ToolMessage(
                        role="tool",
                        tool_call_id=tc.id or "",
                        content=result,
                    )
                )

        texts: list[str] = [
            _text(m).strip()
            for m in messages
            if isinstance(m, AssistantMessage) and m.content
        ]
        if texts:
            return WebSearchOutput(text="\n".join(texts))
        raise RuntimeError("web search completed without usable research text")


def _text(msg: AssistantMessage) -> str:
    content = msg.content
    if content is None or content == "":
        return ""
    if isinstance(content, list):
        return "".join(c.text if hasattr(c, "text") else str(c) for c in content)
    return str(content)
