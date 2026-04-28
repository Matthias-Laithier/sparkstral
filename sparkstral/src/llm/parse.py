from typing import TypeVar

from mistralai.client import Mistral
from pydantic import BaseModel

from .retry import with_llm_retries

ParsedResponseT = TypeVar("ParsedResponseT", bound=BaseModel)


async def parse_chat_model(
    client: Mistral,
    response_model: type[ParsedResponseT],
    *,
    phase: str,
    model: str,
    max_tokens: int,
    temperature: float,
    messages: list[dict[str, str]],
) -> ParsedResponseT:
    async def call() -> ParsedResponseT:
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

    return await with_llm_retries(call, phase=phase)
