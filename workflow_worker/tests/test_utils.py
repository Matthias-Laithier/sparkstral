from datetime import date
from typing import Any, cast

import pytest
from pydantic import BaseModel

import src.utils as utils
from src.agents.web_search import WebSearchAgent, WebSearchInput
from src.config import settings
from src.prompts import web_search_system_prompt


class ParsedExample(BaseModel):
    value: str


class _Message:
    def __init__(self, parsed: BaseModel | None) -> None:
        self.parsed = parsed


class _Choice:
    def __init__(self, parsed: BaseModel | None) -> None:
        self.message = _Message(parsed)


class _Response:
    def __init__(self, parsed: BaseModel | None) -> None:
        self.choices = [_Choice(parsed)]


type Outcome = BaseModel | None | BaseException


class _Chat:
    def __init__(self, outcomes: list[Outcome]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    async def parse_async(self, *_args: Any, **_kwargs: Any) -> _Response:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return _Response(outcome)


class _Client:
    def __init__(self, outcomes: list[Outcome]) -> None:
        self.chat = _Chat(outcomes)


class _CompletionMessage:
    def __init__(self, content: str) -> None:
        self.content = content
        self.tool_calls = None


class _CompletionChoice:
    def __init__(self, message: _CompletionMessage) -> None:
        self.message = message


class _CompletionResponse:
    def __init__(self, message: _CompletionMessage) -> None:
        self.choices = [_CompletionChoice(message)]


type CompletionOutcome = _CompletionResponse | BaseException


class _CompletionChat:
    def __init__(self, outcomes: list[CompletionOutcome]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    async def complete_async(self, *_args: Any, **_kwargs: Any) -> _CompletionResponse:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class _CompletionClient:
    def __init__(self, outcomes: list[CompletionOutcome]) -> None:
        self.chat = _CompletionChat(outcomes)


class _ConversationChunk:
    def __init__(
        self,
        chunk_type: str,
        *,
        text: str | None = None,
        title: str | None = None,
        url: str | None = None,
        source: str | None = None,
    ) -> None:
        self.type = chunk_type
        self.text = text
        self.title = title
        self.url = url
        self.source = source


class _ConversationOutput:
    def __init__(self, output_type: str, content: list[_ConversationChunk]) -> None:
        self.type = output_type
        self.content = content


class _ConversationResponse:
    def __init__(self, outputs: list[_ConversationOutput]) -> None:
        self.outputs = outputs


type ConversationOutcome = _ConversationResponse | BaseException


class _Conversations:
    def __init__(self, outcomes: list[ConversationOutcome]) -> None:
        self.outcomes = outcomes
        self.calls = 0
        self.last_kwargs: dict[str, Any] | None = None

    async def start_async(
        self, *_args: Any, **kwargs: Any
    ) -> _ConversationResponse:
        self.calls += 1
        self.last_kwargs = kwargs
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class _Beta:
    def __init__(self, outcomes: list[ConversationOutcome]) -> None:
        self.conversations = _Conversations(outcomes)


class _ConversationClient:
    def __init__(self, outcomes: list[ConversationOutcome]) -> None:
        self.beta = _Beta(outcomes)


def _skip_retry_delays(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(cast(Any, utils).asyncio, "sleep", sleep)
    monkeypatch.setattr(cast(Any, utils).random, "uniform", lambda _start, _end: 0.0)
    return delays


@pytest.mark.asyncio
async def test_parse_chat_model_returns_parsed_model() -> None:
    parsed = ParsedExample(value="ok")
    client = _Client([parsed])

    result = await utils.parse_chat_model(
        cast(Any, client),
        ParsedExample,
        phase="example",
        model="model",
        max_tokens=100,
        temperature=0,
        messages=[],
    )

    assert result == parsed
    assert client.chat.calls == 1


@pytest.mark.asyncio
async def test_parse_chat_model_retries_after_api_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays = _skip_retry_delays(monkeypatch)
    parsed = ParsedExample(value="ok")
    client = _Client([RuntimeError("transient"), parsed])

    result = await utils.parse_chat_model(
        cast(Any, client),
        ParsedExample,
        phase="example",
        model="model",
        max_tokens=100,
        temperature=0,
        messages=[],
    )

    assert result == parsed
    assert client.chat.calls == 2
    assert delays == [1.0]


@pytest.mark.asyncio
async def test_parse_chat_model_retries_after_missing_parsed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays = _skip_retry_delays(monkeypatch)
    parsed = ParsedExample(value="ok")
    client = _Client([None, parsed])

    result = await utils.parse_chat_model(
        cast(Any, client),
        ParsedExample,
        phase="example",
        model="model",
        max_tokens=100,
        temperature=0,
        messages=[],
    )

    assert result == parsed
    assert client.chat.calls == 2
    assert delays == [1.0]


@pytest.mark.asyncio
async def test_parse_chat_model_raises_after_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays = _skip_retry_delays(monkeypatch)
    client = _Client([None, None, None])

    with pytest.raises(
        RuntimeError,
        match="example failed after 3 attempts",
    ) as exc_info:
        await utils.parse_chat_model(
            cast(Any, client),
            ParsedExample,
            phase="example",
            model="model",
            max_tokens=100,
            temperature=0,
            messages=[],
        )

    assert client.chat.calls == 3
    assert delays == [1.0, 2.0]
    assert isinstance(exc_info.value.__cause__, RuntimeError)


@pytest.mark.asyncio
async def test_web_search_agent_uses_mistral_web_search_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "WEB_SEARCH_PROVIDER", "mistralai")
    response = _ConversationResponse(
        [
            _ConversationOutput(
                "message.output",
                [
                    _ConversationChunk("text", text="research"),
                    _ConversationChunk(
                        "tool_reference",
                        title="Source",
                        url="https://example.com/source",
                    ),
                    _ConversationChunk(
                        "tool_reference",
                        title="Source",
                        url="https://example.com/source",
                    ),
                ],
            )
        ]
    )
    client = _ConversationClient([response])

    result = await WebSearchAgent(cast(Any, client)).run(WebSearchInput(prompt="Acme"))

    assert result.text == "research\n\nSources:\n- Source: https://example.com/source"
    assert client.beta.conversations.calls == 1
    assert client.beta.conversations.last_kwargs == {
        "model": "mistral-small-latest",
        "instructions": web_search_system_prompt(date.today()),
        "inputs": [{"role": "user", "content": "Acme"}],
        "tools": [{"type": "web_search"}],
        "completion_args": {
            "max_tokens": 2048,
            "temperature": 0.0,
        },
        "store": False,
    }


@pytest.mark.asyncio
async def test_web_search_agent_uses_custom_tool_loop_for_tavily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "WEB_SEARCH_PROVIDER", "tavily")
    response = _CompletionResponse(_CompletionMessage("research"))
    client = _CompletionClient([response])

    result = await WebSearchAgent(cast(Any, client)).run(WebSearchInput(prompt="Acme"))

    assert result.text == "research"
    assert client.chat.calls == 1


@pytest.mark.asyncio
async def test_web_search_agent_retries_llm_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays = _skip_retry_delays(monkeypatch)
    response = _CompletionResponse(_CompletionMessage("research"))
    client = _CompletionClient([RuntimeError("transient"), response])

    result = await WebSearchAgent(cast(Any, client)).run(WebSearchInput(prompt="Acme"))

    assert result.text == "research"
    assert client.chat.calls == 2
    assert delays == [1.0]


@pytest.mark.asyncio
async def test_web_search_agent_raises_after_llm_completion_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delays = _skip_retry_delays(monkeypatch)
    client = _CompletionClient(
        [
            RuntimeError("first"),
            RuntimeError("second"),
            RuntimeError("third"),
        ]
    )

    with pytest.raises(
        RuntimeError,
        match="web search llm completion failed after 3 attempts",
    ):
        await WebSearchAgent(cast(Any, client)).run(WebSearchInput(prompt="Acme"))

    assert client.chat.calls == 3
    assert delays == [1.0, 2.0]
