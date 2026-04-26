import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import httpx
from mistralai.client import Mistral
from pydantic import BaseModel

from src.config import settings
from src.schemas import GradedUseCase, PipelineOutput

ResponseT = TypeVar("ResponseT")
ParsedResponseT = TypeVar("ParsedResponseT", bound=BaseModel)

logger = logging.getLogger(__name__)


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


async def with_llm_retries(
    call: Callable[[], Awaitable[ResponseT]],
    *,
    phase: str,
    max_retries: int = 2,
    base_delay_seconds: float = 1.0,
) -> ResponseT:
    attempts = max_retries + 1
    for attempt in range(1, attempts + 1):
        try:
            return await call()
        except Exception as exc:
            if attempt == attempts:
                raise RuntimeError(f"{phase} failed after {attempts} attempts") from exc

            delay_seconds = base_delay_seconds * 2 ** (attempt - 1)
            delay_seconds += random.uniform(0, delay_seconds * 0.1)
            logger.warning(
                "%s failed on attempt %s/%s; retrying in %.2fs: %s",
                phase,
                attempt,
                attempts,
                delay_seconds,
                exc,
            )
            await asyncio.sleep(delay_seconds)

    raise RuntimeError(f"{phase} failed after {attempts} attempts")


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


def _selection_key(
    item: GradedUseCase,
) -> tuple[float, int, int, int, int, int, int, str]:
    return (
        -item.score.weighted_total,
        -item.score.genai_fit,
        -item.score.iconicness,
        -item.score.business_impact,
        -item.score.company_relevance,
        -item.score.feasibility,
        -item.score.evidence_strength,
        item.use_case.id,
    )


def select_top_n(graded: list[GradedUseCase], n: int) -> list[GradedUseCase]:
    ranked = sorted(
        graded,
        key=_selection_key,
    )
    return ranked[:n]


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
