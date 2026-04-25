from datetime import date

from src.prompts import (
    deduper_system_prompt,
    deduper_user_prompt,
    genai_use_cases_system_prompt,
    use_case_grader_system_prompt,
    web_search_system_prompt,
)
from src.schemas import GenAIUseCaseCandidate, GenAIUseCaseCandidatePool


def _candidate(index: int) -> GenAIUseCaseCandidate:
    return GenAIUseCaseCandidate(
        id=f"uc-{index}",
        title=f"Use case {index}",
        target_users=["Ops"],
        business_problem="Problem",
        why_this_company="Company fit",
        genai_solution="Solution",
        required_data="Data",
        expected_impact="Impact",
        why_iconic="Iconic fit",
        feasibility_notes="Feasible with existing records",
        risks=["Risk"],
        linked_opportunities=["Opportunity"],
        evidence_sources=[f"https://example.com/source-{index}"],
        ideation_lens="grounded consultant",
    )


def test_web_search_system_prompt_includes_current_date() -> None:
    prompt = web_search_system_prompt(date(2026, 4, 25))

    assert "2026-04-25" in prompt
    assert "cached_web_search" in prompt


def test_genai_prompt_requires_candidate_pool() -> None:
    prompt = genai_use_cases_system_prompt()

    assert "8-12" in prompt
    assert "candidate pool" in prompt
    assert "grounded consultant" in prompt
    assert "moonshot strategist" in prompt


def test_deduper_prompt_requires_merging_and_evidence_preservation() -> None:
    prompt = deduper_system_prompt()

    assert "6-10" in prompt
    assert "near duplicates" in prompt
    assert "merge" in prompt
    assert "evidence_sources" in prompt
    assert "ideation_lens" in prompt
    assert "company-specific" in prompt
    assert "Do not grade" in prompt


def test_deduper_user_prompt_includes_candidate_json() -> None:
    candidates = GenAIUseCaseCandidatePool(
        use_cases=[_candidate(index) for index in range(1, 9)]
    )

    prompt = deduper_user_prompt(candidates)

    assert "Candidate use-case pool (JSON)" in prompt
    assert "https://example.com/source-1" in prompt
    assert "removed_or_merged" in prompt
    assert "6-10" in prompt


def test_use_case_grader_prompt_includes_explicit_rubric() -> None:
    prompt = use_case_grader_system_prompt()

    assert "company_relevance" in prompt
    assert "business_impact" in prompt
    assert "iconicness" in prompt
    assert "genai_fit" in prompt
    assert "feasibility" in prompt
    assert "evidence_strength" in prompt
    assert "Penalize generic candidates" in prompt
    assert "Do not skip" in prompt
