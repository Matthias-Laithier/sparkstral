import functools
from typing import Any, TypeVar

import httpx
from mistralai.client import Mistral
from pydantic import BaseModel

from src.config import settings
from src.schemas import PipelineOutput

ResponseT = TypeVar("ResponseT", bound=BaseModel)


@functools.cache
def get_mistral_client() -> Mistral:
    return Mistral(
        api_key=settings.MISTRAL_API_KEY,
        async_client=httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(
                connect=10.0,
                read=180.0,
                write=30.0,
                pool=10.0,
            ),
        ),
        timeout_ms=180_000,
    )


def append_text_output(outputs: list[PipelineOutput], text: str) -> None:
    outputs.append(
        PipelineOutput(
            id=len(outputs) + 1,
            kind="text",
            text=text,
        )
    )


def append_json_output(outputs: list[PipelineOutput], data: dict[str, Any]) -> None:
    outputs.append(
        PipelineOutput(
            id=len(outputs) + 1,
            kind="json",
            data=data,
        )
    )


async def parse_chat_model(
    client: Mistral,
    response_model: type[ResponseT],
    *,
    phase: str,
    model: str,
    max_tokens: int,
    temperature: float,
    messages: list[dict[str, str]],
) -> ResponseT:
    parsed = await client.chat.parse_async(
        response_model,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    if (
        parsed.choices
        and parsed.choices[0].message
        and parsed.choices[0].message.parsed is not None
    ):
        return parsed.choices[0].message.parsed
    raise RuntimeError(f"{phase} returned no parsed output")
