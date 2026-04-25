import json
from datetime import date
from typing import Any, cast

from mistralai.client.models import AssistantMessage, ToolMessage
from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import web_search_system_prompt
from src.tools.cached_web_search import CACHED_WEB_SEARCH_TOOL, cached_web_search
from src.utils import with_llm_retries


class WebSearchInput(BaseModel):
    prompt: str


class WebSearchOutput(BaseModel):
    text: str


class WebSearchAgent(BaseAgent[WebSearchInput, WebSearchOutput]):
    name = "web-search"

    async def run(self, params: WebSearchInput) -> WebSearchOutput:
        if settings.WEB_SEARCH_PROVIDER == "mistralai":
            return await self._run_mistralai(params)
        return await self._run_custom_search_tool(params)

    async def _run_custom_search_tool(self, params: WebSearchInput) -> WebSearchOutput:
        messages: list[Any] = [
            {"role": "system", "content": web_search_system_prompt(date.today())},
            {"role": "user", "content": params.prompt},
        ]

        for _ in range(settings.WEB_SEARCH_MAX_ROUNDS):
            response = await with_llm_retries(
                lambda: self.client.chat.complete_async(
                    model=settings.WEB_SEARCH_MODEL,
                    messages=messages,
                    tools=[cast(Any, CACHED_WEB_SEARCH_TOOL)],
                    tool_choice="auto",
                    max_tokens=settings.LLM_MAX_TOKENS,
                    temperature=settings.LLM_TEMPERATURE,
                ),
                phase="web search llm completion",
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

    async def _run_mistralai(self, params: WebSearchInput) -> WebSearchOutput:
        response = await with_llm_retries(
            lambda: self.client.beta.conversations.start_async(
                model=settings.WEB_SEARCH_MODEL,
                instructions=web_search_system_prompt(date.today()),
                inputs=cast(Any, [{"role": "user", "content": params.prompt}]),
                tools=cast(Any, [{"type": "web_search"}]),
                completion_args={
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "temperature": settings.LLM_TEMPERATURE,
                },
                store=False,
            ),
            phase="mistral web search conversation",
        )
        text = _conversation_text(response).strip()
        if not text:
            raise RuntimeError("mistral web search returned no usable research text")
        return WebSearchOutput(text=text)


def _text(msg: AssistantMessage) -> str:
    content = msg.content
    if content is None or content == "":
        return ""
    if isinstance(content, list):
        return "".join(c.text if hasattr(c, "text") else str(c) for c in content)
    return str(content)


def _conversation_text(response: Any) -> str:
    parts: list[str] = []
    references: list[str] = []
    outputs = _value(response, "outputs")
    if not isinstance(outputs, list):
        return ""

    for output in outputs:
        if _value(output, "type") != "message.output":
            continue
        _append_conversation_content(_value(output, "content"), parts, references)

    body = "".join(parts).strip()
    references = _unique(references)
    if not references:
        return body

    sources = "\n".join(f"- {reference}" for reference in references)
    if body:
        return f"{body}\n\nSources:\n{sources}"
    return f"Sources:\n{sources}"


def _append_conversation_content(
    content: Any,
    parts: list[str],
    references: list[str],
) -> None:
    if content is None:
        return
    if isinstance(content, str):
        parts.append(content)
        return
    if isinstance(content, list):
        for chunk in content:
            _append_conversation_chunk(chunk, parts, references)
        return
    _append_conversation_chunk(content, parts, references)


def _append_conversation_chunk(
    chunk: Any,
    parts: list[str],
    references: list[str],
) -> None:
    chunk_type = _value(chunk, "type")
    if chunk_type == "tool_reference":
        reference = _tool_reference(chunk)
        if reference:
            references.append(reference)
        return

    text = _value(chunk, "text")
    if text is not None:
        parts.append(str(text))
        return
    if isinstance(chunk, str):
        parts.append(chunk)


def _tool_reference(chunk: Any) -> str | None:
    title = _value(chunk, "title")
    url = _value(chunk, "url")
    source = _value(chunk, "source")

    if title and url:
        return f"{title}: {url}"
    if url:
        return str(url)
    if title and source:
        return f"{title}: {source}"
    if source:
        return str(source)
    if title:
        return str(title)
    return None


def _value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _unique(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        unique_values.append(value)
        seen.add(value)
    return unique_values
