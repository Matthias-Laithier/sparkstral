from src.core.schemas import GradedUseCase


def _selection_key(
    item: GradedUseCase,
) -> tuple[float, int, int, int, int, int, int, str]:
    s = item.score
    return (
        -s.weighted_total,
        -s.genai_fit.score,
        -s.iconicness.score,
        -s.business_impact.score,
        -s.company_relevance.score,
        -s.feasibility.score,
        -s.evidence_strength.score,
        item.use_case.id,
    )


def select_top_n(
    graded: list[GradedUseCase],
    n: int,
) -> list[GradedUseCase]:
    ranked = sorted(graded, key=_selection_key)
    return ranked[:n]
