import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

ResponseT = TypeVar("ResponseT")

logger = logging.getLogger(__name__)


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

    raise AssertionError("unreachable: loop always returns or raises")
