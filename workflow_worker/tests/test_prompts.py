from datetime import date

from src.prompts import (
    genai_use_cases_system_prompt,
    genai_use_cases_user_prompt,
    markdown_reporter_system_prompt,
    markdown_reporter_user_prompt,
    use_case_grader_system_prompt,
    web_search_system_prompt,
)
from src.schemas import (
    CompanyProfileOutput,
    EvidenceItem,
    FinalSelectionOutput,
    GenAIMechanism,
    GenAIUseCaseCandidate,
    GradedUseCase,
    PainPointItem,
    PainPointProfilerOutput,
    UseCaseScore,
)


def _genai_mechanism() -> GenAIMechanism:
    return GenAIMechanism(
        mechanisms=["document_understanding", "structured_generation"],
        why_genai_is_needed="The workflow needs document reasoning and generation.",
        why_classical_software_is_not_enough=(
            "Rules alone cannot synthesize messy operational context."
        ),
        why_classical_ml_or_optimization_is_not_enough=(
            "A predictor or optimizer would not draft grounded recommendations."
        ),
    )


def _candidate(index: int) -> GenAIUseCaseCandidate:
    return GenAIUseCaseCandidate(
        id=f"uc-{index}",
        title=f"Use case {index}",
        target_users=["Ops"],
        business_problem="Problem",
        why_this_company="Company fit",
        genai_solution="Solution",
        genai_mechanism=_genai_mechanism(),
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
    assert "GenAI-native" in prompt
    assert "predictive maintenance" in prompt
    assert "numerical forecasting" in prompt
    assert "process optimization" in prompt
    assert "control systems" in prompt
    assert "dashboards" in prompt
    assert "generic RAG" in prompt
    assert "generic chatbot" in prompt
    assert "why classical ML or optimization is not enough" in prompt


def test_genai_user_prompt_requires_mechanism_and_workflow() -> None:
    prompt = genai_use_cases_user_prompt(_company_profile(), _pain_points())

    assert "genai_mechanism" in prompt
    assert "mechanisms (1+)" in prompt
    assert "three why_* fields" in prompt
    assert "who uses it" in prompt
    assert "what they input" in prompt
    assert "what the system generates" in prompt
    assert "human approval step" in prompt


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


def test_markdown_reporter_prompt_requires_client_ready_markdown() -> None:
    prompt = markdown_reporter_system_prompt()

    assert "client-ready" in prompt
    assert "`markdown` field" in prompt
    assert "complete markdown report" in prompt
    assert "finished consulting deliverable" in prompt
    assert "selection methodology" in prompt
    assert "ranked recommendations table" in prompt
    assert "detailed sections for each of the 3 use cases" in prompt
    assert "rank 1, rank 2, and rank 3" in prompt
    assert "score totals" in prompt
    assert "Why this is GenAI" in prompt
    assert "genai_mechanism" in prompt
    assert "source URLs" in prompt
    assert "Do not invent" in prompt


def test_markdown_reporter_user_prompt_includes_direct_input_json() -> None:
    prompt = markdown_reporter_user_prompt(
        _company_profile(),
        _pain_points(),
        _final_selection(),
    )

    assert "Company profile (JSON)" in prompt
    assert "Pain point analysis (JSON)" in prompt
    assert "Selected top 3 use cases with scores (JSON)" in prompt
    assert '"company_name": "Acme Corporation"' in prompt
    assert '"id": "uc-1"' in prompt
    assert '"genai_mechanism": {' in prompt
    assert '"document_understanding"' in prompt
    assert '"score": {' in prompt
    assert "Write the final client-ready markdown report" in prompt
    assert "Use these JSON inputs as the source of truth" in prompt
    assert "ranked recommendations table" in prompt
    assert "Why this is GenAI" in prompt
    assert "caveats" in prompt
    assert "do not include raw JSON" in prompt
