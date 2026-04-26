from datetime import date

from src.prompts import (
    genai_use_cases_system_prompt,
    genai_use_cases_user_prompt,
    markdown_reporter_system_prompt,
    markdown_reporter_user_prompt,
    use_case_grader_system_prompt,
    use_case_grader_user_prompt,
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
    PilotKPI,
    SourceBackedMetric,
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


def _source_backed_metric(source_url: str) -> SourceBackedMetric:
    return SourceBackedMetric(
        label="Pain prominence",
        value="Prominence 8 of 10",
        source_url=source_url,
        source_quote_or_evidence="The source supports the pain point prominence.",
        applies_to="company",
        confidence="medium",
    )


def _pilot_kpis() -> list[PilotKPI]:
    return [
        PilotKPI(
            kpi="Manual review cycle time",
            why_it_matters="Shows whether the workflow speeds up expert review.",
            measurement_method="Compare cycle time before and during the pilot.",
            target_direction="decrease",
            baseline_needed="Current median review cycle time.",
        ),
        PilotKPI(
            kpi="Accepted recommendations",
            why_it_matters="Shows whether generated outputs are useful to reviewers.",
            measurement_method="Track reviewer acceptance rate during the pilot.",
            target_direction="increase",
            baseline_needed=(
                "Current acceptance rate for manually drafted recommendations."
            ),
        ),
    ]


def _candidate(index: int) -> GenAIUseCaseCandidate:
    evidence_source = f"https://example.com/source-{index}"
    return GenAIUseCaseCandidate(
        id=f"uc-{index}",
        title=f"Use case {index}",
        target_users=["Ops"],
        business_problem="Problem",
        why_this_company="Company fit",
        genai_solution="Solution",
        genai_mechanism=_genai_mechanism(),
        required_data="Data",
        qualitative_impact="Qualitative impact",
        source_backed_metrics=[_source_backed_metric(evidence_source)],
        pilot_kpis=_pilot_kpis(),
        why_iconic="Iconic fit",
        feasibility_notes="Feasible with existing records",
        risks=["Risk"],
        linked_pain_points=["Pain 1"],
        evidence_sources=[evidence_source],
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
        strengths=["Strength"],
        weaknesses=["Weakness"],
        rationale="Rationale",
        company_relevance=3,
        business_impact=3,
        iconicness=3,
        genai_fit=3,
        feasibility=3,
        evidence_strength=3,
        penalties=[],
        weighted_total=3.0,
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
    assert "Do not invent numeric impact" in prompt
    assert "source_backed_metrics" in prompt
    assert "pilot_kpis" in prompt


def test_genai_user_prompt_requires_mechanism_and_workflow() -> None:
    prompt = genai_use_cases_user_prompt(_company_profile(), _pain_points())

    assert "genai_mechanism" in prompt
    assert "mechanisms (1+)" in prompt
    assert "three why_* fields" in prompt
    assert "who uses it" in prompt
    assert "what they input" in prompt
    assert "what the system generates" in prompt
    assert "human approval step" in prompt
    assert "qualitative_impact" in prompt
    assert "source_backed_metrics" in prompt
    assert "pilot_kpis (2+)" in prompt
    assert "do not invent target values" in prompt


def test_use_case_grader_prompt_includes_explicit_rubric() -> None:
    prompt = use_case_grader_system_prompt()

    assert "company_relevance" in prompt
    assert "business_impact" in prompt
    assert "iconicness" in prompt
    assert "genai_fit" in prompt
    assert "feasibility" in prompt
    assert "evidence_strength" in prompt
    assert "Scores of 5 should be rare" in prompt
    assert "Generic chatbot, RAG, internal knowledge assistant" in prompt
    assert "classical ML, forecasting, optimization" in prompt
    assert "Unsupported metrics" in prompt
    assert "Vague target users" in prompt
    assert "penalties" in prompt
    assert "use_case_id" in prompt
    assert "Do not repeat or rewrite the original use_case objects" in prompt
    assert "Do not output weighted_total" in prompt
    assert "application code will compute" in prompt
    assert "Do not skip" in prompt


def test_use_case_grader_user_prompt_requests_score_only_output() -> None:
    prompt = use_case_grader_user_prompt(
        _company_profile(),
        _pain_points(),
        [_candidate(1), _candidate(2)],
    )

    assert "Generated use cases to grade (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert "Return one grades item for every use case above" in prompt
    assert "use_case_id equal to the matching use_case.id" in prompt
    assert "Do not repeat, copy, or rewrite any original use_case object" in prompt
    assert "Do not output weighted_total" in prompt
    assert "Return one graded_use_cases item" not in prompt
    assert "Keep each original use_case object unchanged" not in prompt


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
    assert "weighted scores" in prompt
    assert "Why this is GenAI" in prompt
    assert "genai_mechanism" in prompt
    assert "source URLs" in prompt
    assert "Do not invent" in prompt
    assert "Expected Impact and KPIs" in prompt
    assert "source-backed metrics separately from pilot KPIs" in prompt
    assert "pilot results show" in prompt
    assert "lab data shows" in prompt
    assert "will reduce by" in prompt
    assert "will improve by" in prompt


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
    assert '"qualitative_impact": "Qualitative impact"' in prompt
    assert '"source_backed_metrics": [' in prompt
    assert '"pilot_kpis": [' in prompt
    assert '"score": {' in prompt
    assert "Write the final client-ready markdown report" in prompt
    assert "Use these JSON inputs as the source of truth" in prompt
    assert "ranked recommendations table" in prompt
    assert "Expected Impact and KPIs" in prompt
    assert "Why this is GenAI" in prompt
    assert "caveats" in prompt
    assert "do not include raw JSON" in prompt
