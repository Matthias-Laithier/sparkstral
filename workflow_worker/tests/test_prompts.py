from datetime import date

from src.prompts import (
    final_reporter_system_prompt,
    final_reporter_user_prompt,
    genai_use_cases_system_prompt,
    markdown_reporter_system_prompt,
    markdown_reporter_user_prompt,
    use_case_grader_system_prompt,
    web_search_system_prompt,
)
from src.schemas import (
    CompanyProfileOutput,
    EvidenceItem,
    FinalReport,
    FinalReportUseCase,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    GradedUseCase,
    PainPointItem,
    PainPointProfilerOutput,
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
        linked_pain_points=["Pain 1"],
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


def _final_selection() -> FinalSelectionOutput:
    return FinalSelectionOutput(selected=_graded_use_cases()[:3])


def _final_report_use_case(item: GradedUseCase, rank: int) -> FinalReportUseCase:
    use_case = item.use_case
    return FinalReportUseCase(
        rank=rank,
        title=use_case.title,
        one_liner=f"{use_case.title} one-liner",
        target_users=use_case.target_users,
        business_problem=use_case.business_problem,
        why_this_company=use_case.why_this_company,
        genai_solution=use_case.genai_solution,
        required_data=use_case.required_data,
        expected_impact=use_case.expected_impact,
        why_iconic=use_case.why_iconic,
        feasibility_notes=use_case.feasibility_notes,
        risks=use_case.risks,
        score=item.score,
        source_urls=use_case.evidence_sources,
    )


def _final_report() -> FinalReport:
    return FinalReport(
        company_name="Acme Corporation",
        executive_summary="Top three use cases are ready for client discussion.",
        company_context="Acme is a manufacturing company focused on widgets.",
        methodology="Candidates were generated, scored once, and selected.",
        top_3_use_cases=[
            _final_report_use_case(item, rank)
            for rank, item in enumerate(_final_selection().selected, start=1)
        ],
        caveats=["Validate data access before implementation."],
        source_urls=["https://example.com/company", "https://example.com/source-1"],
    )


def test_web_search_system_prompt_includes_current_date() -> None:
    prompt = web_search_system_prompt(date(2026, 4, 25))

    assert "2026-04-25" in prompt
    assert "web search" in prompt


def test_genai_prompt_requires_candidate_pool() -> None:
    prompt = genai_use_cases_system_prompt()

    assert "8-12" in prompt
    assert "candidate pool" in prompt
    assert "grounded consultant" in prompt
    assert "moonshot strategist" in prompt


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


def test_final_reporter_prompt_requires_client_ready_report() -> None:
    prompt = final_reporter_system_prompt()

    assert "client-ready" in prompt
    assert "exactly 3 use cases" in prompt
    assert "score breakdown" in prompt
    assert "scoring" in prompt
    assert "supplied artifacts" in prompt
    assert "use-case generation" in prompt
    assert "final top-3 selection" in prompt
    assert "high-impact" in prompt
    assert "iconic" in prompt
    assert "source URLs" in prompt
    assert "Do not write markdown" in prompt


def test_final_reporter_user_prompt_includes_final_selection_json() -> None:
    prompt = final_reporter_user_prompt(
        _company_profile(),
        _pain_points(),
        _final_selection(),
    )

    assert "Final top 3 selected use cases with scores (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert '"score": {' in prompt
    assert "Return exactly 3 top_3_use_cases" in prompt
    assert "rank 1, rank 2, and rank 3" in prompt
    assert "source_urls" in prompt
    assert "methodology" in prompt
    assert "single scoring pass" in prompt


def test_markdown_reporter_prompt_requires_client_ready_markdown() -> None:
    prompt = markdown_reporter_system_prompt()

    assert "client-ready" in prompt
    assert "`markdown` field" in prompt
    assert "complete markdown report" in prompt
    assert "finished consulting deliverable" in prompt
    assert "rank order" in prompt
    assert "score totals" in prompt
    assert "source URLs" in prompt
    assert "Do not invent" in prompt


def test_markdown_reporter_user_prompt_includes_structured_report_json() -> None:
    prompt = markdown_reporter_user_prompt(_final_report())

    assert "Structured final report JSON" in prompt
    assert '"company_name": "Acme Corporation"' in prompt
    assert '"top_3_use_cases": [' in prompt
    assert "Write the final client-ready markdown report" in prompt
    assert "Use the JSON as the source of truth" in prompt
    assert "do not include raw JSON" in prompt
