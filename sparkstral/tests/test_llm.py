from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

import src.llm.retry as llm_retry
from src.llm import parse_chat_model


class _Parsed(BaseModel):
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


def _make_client(outcomes: list[BaseModel | None | BaseException]) -> Any:
    call_count = 0

    async def parse_async(*_a: Any, **_kw: Any) -> _Response:
        nonlocal call_count
        call_count += 1
        outcome = outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return _Response(outcome)

    client = AsyncMock()
    client.chat.parse_async = parse_async
    client._call_count = lambda: call_count
    return client


def _skip_delays(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cast(Any, llm_retry).asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(cast(Any, llm_retry).random, "uniform", lambda _s, _e: 0.0)


@pytest.mark.asyncio
async def test_parse_chat_model_returns_on_success() -> None:
    parsed = _Parsed(value="ok")
    client = _make_client([parsed])

    result = await parse_chat_model(
        client,
        _Parsed,
        phase="test",
        model="m",
        max_tokens=1,
        temperature=0,
        messages=[],
    )

    assert result == parsed


@pytest.mark.asyncio
async def test_parse_chat_model_retries_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_delays(monkeypatch)
    parsed = _Parsed(value="ok")
    client = _make_client([RuntimeError("transient"), parsed])

    result = await parse_chat_model(
        client,
        _Parsed,
        phase="test",
        model="m",
        max_tokens=1,
        temperature=0,
        messages=[],
    )

    assert result == parsed
    assert client._call_count() == 2


@pytest.mark.asyncio
async def test_parse_chat_model_raises_after_exhausting_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_delays(monkeypatch)
    client = _make_client([RuntimeError("a"), RuntimeError("b"), RuntimeError("c")])

    with pytest.raises(RuntimeError, match="test failed after 3 attempts"):
        await parse_chat_model(
            client,
            _Parsed,
            phase="test",
            model="m",
            max_tokens=1,
            temperature=0,
            messages=[],
        )
