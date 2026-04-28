from src.agents.grader import compute_weighted_total
from src.utils.selection import select_top_n

from .factories import make_graded, make_score


def test_select_top_n_picks_highest_scores() -> None:
    graded = [make_graded(i, weighted_total=float(i)) for i in range(1, 6)]

    result = select_top_n(graded, 3)

    assert [item.use_case.id for item in result] == ["uc_5", "uc_4", "uc_3"]


def test_select_top_n_skips_same_domain() -> None:
    graded = [
        make_graded(1, weighted_total=9.0, domain="water"),
        make_graded(2, weighted_total=8.0, domain="water"),
        make_graded(3, weighted_total=7.0, domain="energy"),
        make_graded(4, weighted_total=6.0, domain="waste"),
        make_graded(5, weighted_total=5.0, domain="logistics"),
    ]

    result = select_top_n(graded, 3)

    assert [item.use_case.id for item in result] == ["uc_1", "uc_3", "uc_4"]


def test_compute_weighted_total_formula() -> None:
    score = make_score(
        "uc_1",
        iconicness=6,
        genai_fit=4,
        business_impact=8,
        company_relevance=10,
        feasibility=2,
        evidence_strength=10,
    )

    assert compute_weighted_total(score) == round(
        0.25 * 6 + 0.25 * 4 + 0.20 * 8 + 0.15 * 10 + 0.08 * 2 + 0.07 * 10, 2
    )
