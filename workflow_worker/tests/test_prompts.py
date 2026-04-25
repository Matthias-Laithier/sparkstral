from datetime import date

from src.prompts import (
    deduper_system_prompt,
    deduper_user_prompt,
    final_reporter_system_prompt,
    final_reporter_user_prompt,
    genai_use_cases_system_prompt,
    red_team_system_prompt,
    red_team_user_prompt,
    refiner_system_prompt,
    refiner_user_prompt,
    use_case_grader_system_prompt,
    web_search_system_prompt,
)
from src.schemas import (
    CompanyProfileOutput,
    EvidenceItem,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidatePool,
    GradedUseCase,
    OpportunityItem,
    OpportunityMapOutput,
    PainPointItem,
    PainPointProfilerOutput,
    RedTeamOutput,
    RedTeamReview,
    UseCaseCriticism,
    UseCaseScore,
)


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


def _company_profile() -> CompanyProfileOutput:
    return CompanyProfileOutput(
        company_name="Acme Corporation",
        industry="Manufacturing",
        business_lines=["Widgets"],
        key_customers=["Industrial buyers"],
        strategic_priorities=["Operational efficiency"],
        evidence=[
            EvidenceItem(
                claim="Acme makes widgets",
                source="https://example.com/company",
            )
        ],
        notes="No caveats.",
    )


def _pain_point(index: int) -> PainPointItem:
    return PainPointItem(
        title=f"Pain {index}",
        description="Description",
        prominence=8,
        sources=[f"https://example.com/pain-{index}"],
    )


def _pain_points() -> PainPointProfilerOutput:
    return PainPointProfilerOutput(
        pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
    )


def _opportunity(index: int) -> OpportunityItem:
    return OpportunityItem(
        title=f"Opportunity {index}",
        business_line="Widgets",
        linked_pain_points=[f"Pain {index}"],
        why_it_matters="Why it matters",
        why_genai_is_suitable="GenAI can reason across unstructured records.",
        likely_data_sources=["Work orders"],
        evidence_sources=[f"https://example.com/pain-{index}"],
    )


def _opportunity_map() -> OpportunityMapOutput:
    return OpportunityMapOutput(
        opportunities=[_opportunity(1), _opportunity(2), _opportunity(3)],
        summary="Opportunity summary",
    )


def _score(use_case_id: str) -> UseCaseScore:
    return UseCaseScore(
        use_case_id=use_case_id,
        company_relevance=3,
        business_impact=3,
        iconicness=3,
        genai_fit=3,
        feasibility=3,
        evidence_strength=3,
        total=18,
        rationale="Rationale",
        strengths=["Strength"],
        weaknesses=["Weakness"],
    )


def _graded_use_cases() -> list[GradedUseCase]:
    return [
        GradedUseCase(
            use_case=_candidate(index),
            score=_score(f"uc-{index}"),
        )
        for index in range(1, 6)
    ]


def _red_team_output() -> RedTeamOutput:
    return RedTeamOutput(
        reviews=[
            RedTeamReview(
                use_case_id=f"uc-{index}",
                criticisms=[
                    UseCaseCriticism(
                        title=f"Weakness {index}",
                        comment="The expected impact is too vague.",
                        severity="high" if index == 1 else "medium",
                        required_fix="Make the impact concrete without new facts.",
                    )
                ],
                verdict="revise",
            )
            for index in range(1, 6)
        ]
    )


def _final_selection() -> FinalSelectionOutput:
    return FinalSelectionOutput(selected=_graded_use_cases()[:3])


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


def test_red_team_prompt_requires_critique_only() -> None:
    prompt = red_team_system_prompt()

    assert "red-team critic" in prompt
    assert "Do not rewrite" in prompt
    assert "generic ideas" in prompt
    assert "unsupported claims" in prompt
    assert "weak feasibility" in prompt
    assert "unclear business impact" in prompt
    assert "do not really need GenAI" in prompt


def test_red_team_user_prompt_includes_selected_top_five_json() -> None:
    prompt = red_team_user_prompt(
        _company_profile(),
        _pain_points(),
        _opportunity_map(),
        _graded_use_cases(),
    )

    assert "Initial top 5 selected use cases to red-team (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert '"id": "uc-5"' in prompt
    assert "Return exactly 5 reviews" in prompt
    assert "one per selected use case" in prompt
    assert "do not rewrite use cases" in prompt


def test_refiner_prompt_requires_red_team_driven_refinement() -> None:
    prompt = refiner_system_prompt()

    assert "red-team criticism" in prompt
    assert "Fix high-severity issues" in prompt
    assert "company fit more specific" in prompt
    assert "expected impact more operationally specific" in prompt
    assert "Preserve evidence" in prompt
    assert "unresolved_concerns" in prompt


def test_refiner_user_prompt_includes_selected_use_cases_and_red_team_json() -> None:
    prompt = refiner_user_prompt(
        _company_profile(),
        _pain_points(),
        _opportunity_map(),
        _graded_use_cases(),
        _red_team_output(),
    )

    assert "Initial top 5 selected use cases to refine (JSON)" in prompt
    assert "Red-team review to address (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert '"use_case_id": "uc-5"' in prompt
    assert "Return exactly 5 refined_use_cases" in prompt
    assert "original_use_case_id" in prompt
    assert "changes_made" in prompt
    assert "unresolved_concerns" in prompt
    assert "Preserve all original evidence_sources URLs" in prompt


def test_final_reporter_prompt_requires_client_ready_report() -> None:
    prompt = final_reporter_system_prompt()

    assert "client-ready" in prompt
    assert "exactly 3 use cases" in prompt
    assert "score breakdown" in prompt
    assert "scoring" in prompt
    assert "supplied artifacts" in prompt
    assert "refinement" in prompt
    assert "final top-3 selection" in prompt
    assert "high-impact" in prompt
    assert "iconic" in prompt
    assert "source URLs" in prompt
    assert "Do not write markdown" in prompt


def test_final_reporter_user_prompt_includes_final_selection_json() -> None:
    prompt = final_reporter_user_prompt(
        _company_profile(),
        _pain_points(),
        _opportunity_map(),
        _final_selection(),
    )

    assert "Final top 3 selected use cases with scores (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert '"score": {' in prompt
    assert "Return exactly 3 top_3_use_cases" in prompt
    assert "rank 1, rank 2, and rank 3" in prompt
    assert "source_urls" in prompt
    assert "methodology" in prompt
    assert "scoring and refinement loop" in prompt
