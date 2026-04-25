from typing import Any

import pytest
from pydantic import BaseModel

from src.utils import parse_chat_model


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


class _Chat:
    def __init__(self, parsed: BaseModel | None) -> None:
        self.parsed = parsed

    async def parse_async(self, *_args: Any, **_kwargs: Any) -> _Response:
        return _Response(self.parsed)


class _Client:
    def __init__(self, parsed: BaseModel | None) -> None:
        self.chat = _Chat(parsed)


@pytest.mark.asyncio
async def test_parse_chat_model_returns_parsed_model() -> None:
    parsed = ParsedExample(value="ok")

    result = await parse_chat_model(
        _Client(parsed),
        ParsedExample,
        phase="example",
        model="model",
        max_tokens=100,
        temperature=0,
        messages=[],
    )

    assert result == parsed


@pytest.mark.asyncio
async def test_parse_chat_model_raises_when_no_parsed_model() -> None:
    with pytest.raises(RuntimeError, match="example returned no parsed output"):
        await parse_chat_model(
            _Client(None),
            ParsedExample,
            phase="example",
            model="model",
            max_tokens=100,
            temperature=0,
            messages=[],
        )
