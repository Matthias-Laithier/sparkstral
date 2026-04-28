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


def _signal_overlap(a: GradedUseCase, b: GradedUseCase) -> float:
    """Jaccard similarity between company_signal_labels of two use cases."""
    set_a = {label.lower() for label in a.use_case.company_signal_labels}
    set_b = {label.lower() for label in b.use_case.company_signal_labels}
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _same_domain(a: GradedUseCase, b: GradedUseCase) -> bool:
    return (
        a.use_case.business_domain.strip().lower()
        == b.use_case.business_domain.strip().lower()
    )


def select_top_n(
    graded: list[GradedUseCase],
    n: int,
    *,
    overlap_threshold: float = 0.5,
) -> list[GradedUseCase]:
    ranked = sorted(graded, key=_selection_key)
    selected: list[GradedUseCase] = []
    for candidate in ranked:
        if len(selected) >= n:
            break
        if any(
            _same_domain(candidate, picked)
            or _signal_overlap(candidate, picked) >= overlap_threshold
            for picked in selected
        ):
            continue
        selected.append(candidate)
    if len(selected) < n:
        for candidate in ranked:
            if len(selected) >= n:
                break
            if candidate not in selected:
                selected.append(candidate)
    return selected
