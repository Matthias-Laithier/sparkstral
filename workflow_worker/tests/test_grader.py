import pytest

from src.agents.grader import (
    build_graded_use_case_pool,
    build_single_use_case_grade_inputs,
    compute_weighted_total,
)

from .factories import make_candidate, make_grade_result, make_profile


def test_peer_summaries_exclude_self() -> None:
    profile = make_profile()
    use_cases = [make_candidate(i) for i in range(1, 4)]

    inputs = build_single_use_case_grade_inputs(profile, use_cases)

    for grade_input in inputs:
        own_id = grade_input.use_case.id
        for summary in grade_input.peer_summaries:
            assert not summary.startswith(f"{own_id}:")
        assert len(grade_input.peer_summaries) == len(use_cases) - 1


def test_duplicate_ids_rejected() -> None:
    profile = make_profile()
    uc = make_candidate(1)
    duplicate = make_candidate(1)

    with pytest.raises(ValueError, match="duplicate IDs"):
        build_single_use_case_grade_inputs(profile, [uc, duplicate])


def test_build_graded_pool_applies_weighted_totals() -> None:
    use_cases = [make_candidate(i) for i in range(1, 4)]
    grades = [
        make_grade_result(f"uc_{i}", iconicness=i * 2, genai_fit=i * 2)
        for i in range(1, 4)
    ]

    pool = build_graded_use_case_pool(use_cases, grades)

    for item in pool.graded_use_cases:
        assert item.score.weighted_total == compute_weighted_total(item.score)
        assert item.score.weighted_total > 0
    assert "Thinking for uc_1" in pool.grader_thinking
