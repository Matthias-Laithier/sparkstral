from typing import Any, Literal

from src.workflow.schemas import SparkstralStep


def append_sparkstral_step(
    steps: list[SparkstralStep],
    *,
    label: str,
    phase: Literal["research", "structure"],
    content: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Append a `SparkstralStep` with `id` = `len(steps) + 1` before the append."""
    next_id = len(steps) + 1
    steps.append(
        SparkstralStep(
            id=next_id,
            label=label,
            phase=phase,
            content=content,
            data=data,
        )
    )
