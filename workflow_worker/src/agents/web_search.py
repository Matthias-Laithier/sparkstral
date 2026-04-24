import json
from datetime import date
from typing import Any, cast

from mistralai.client.models import AssistantMessage, ToolMessage
from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.config import settings
from src.tools.cached_web_search import CACHED_WEB_SEARCH_TOOL, cached_web_search


class WebSearchInput(BaseModel):
    prompt: str


class WebSearchOutput(BaseModel):
    text: str


class WebSearchAgent(BaseAgent):
    name = "web-search"
    system_prompt = (
        "You are a research assistant. Use cached_web_search to find accurate,"
        " up-to-date information. Cite the source URL for every fact you report. "
        "You have to be concise and to the point."
    )

    async def run(self, input: WebSearchInput) -> WebSearchOutput:  # type: ignore[override]
        today = date.today().strftime("%Y-%m-%d")
        system = (
            f"{self.system_prompt} The current date is {today}. "
            "Use that date for you web searches as it will give you the most up to date information."
        )
        messages: list[Any] = [
            {"role": "system", "content": system},
            {"role": "user", "content": input.prompt},
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
                return WebSearchOutput(text=_text(msg))

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

        # Fallback: concatenate any assistant text collected so far
        texts: list[str] = [
            _text(m) for m in messages if isinstance(m, AssistantMessage) and m.content
        ]
        return WebSearchOutput(text="\n".join(texts))


def _text(msg: AssistantMessage) -> str:
    content = msg.content
    if content is None or content == "":
        return ""
    if isinstance(content, list):
        return "".join(c.text if hasattr(c, "text") else str(c) for c in content)
    return str(content)
