from typing import Any, cast

import pytest
from pydantic import ValidationError

from src import activities, pipeline
from src.agents import final_reporter, grader, markdown_reporter
from src.agents.final_reporter import FinalReporterAgent
from src.agents.grader import UseCaseGraderAgent, compute_total_score
from src.agents.markdown_reporter import MarkdownReporterAgent
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    CompanyResolutionOutput,
    EvidenceItem,
    FinalReport,
    FinalReportInput,
    FinalReportUseCase,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidatePool,
    GradedUseCase,
    GradedUseCasePool,
    GradeUseCasesInput,
    MarkdownReport,
    MarkdownReportInput,
    PainPointItem,
    PainPointProfilerOutput,
    ResearchResult,
    SparkstralWorkflowResult,
    UseCaseScore,
)
from src.utils import select_top_n

IDEATION_LENSES = (
    "grounded consultant",
    "moonshot strategist",
    "operations expert",
    "customer/partner expert",
    "risk/compliance expert",
)


def _company_resolution() -> CompanyResolutionOutput:
    return CompanyResolutionOutput(
        input_name="Acme",
        resolved_name="Acme Corporation",
        website="https://example.com",
        headquarters_country="United States",
        primary_industry="Manufacturing",
        ambiguity_notes="Acme Corporation is the likely match.",
        confidence=0.9,
        evidence=[
            EvidenceItem(
                claim="Acme Corporation is a manufacturing company",
                source="https://example.com/company",
            )
        ],
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


def _candidate(index: int) -> GenAIUseCaseCandidate:
    pain_point_index = ((index - 1) % 3) + 1
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
        linked_pain_points=[f"Pain {pain_point_index}"],
        evidence_sources=[f"https://example.com/pain-{pain_point_index}"],
        ideation_lens=IDEATION_LENSES[(index - 1) % len(IDEATION_LENSES)],
    )


def _candidate_pool() -> GenAIUseCaseCandidatePool:
    return GenAIUseCaseCandidatePool(
        use_cases=[_candidate(index) for index in range(1, 9)]
    )


def _score(
    use_case_id: str,
    *,
    company_relevance: int = 3,
    business_impact: int = 3,
    iconicness: int = 3,
    genai_fit: int = 3,
    feasibility: int = 3,
    evidence_strength: int = 3,
    total: int | None = None,
) -> UseCaseScore:
    computed_total = (
        company_relevance
        + business_impact
        + iconicness
        + genai_fit
        + feasibility
        + evidence_strength
    )
    return UseCaseScore(
        use_case_id=use_case_id,
        company_relevance=company_relevance,
        business_impact=business_impact,
        iconicness=iconicness,
        genai_fit=genai_fit,
        feasibility=feasibility,
        evidence_strength=evidence_strength,
        total=computed_total if total is None else total,
        rationale="Rationale",
        strengths=["Strength"],
        weaknesses=["Weakness"],
    )


def _graded_pool(use_cases: list[GenAIUseCaseCandidate]) -> GradedUseCasePool:
    return GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=use_case,
                score=_score(
                    use_case.id,
                    company_relevance=5 if index == 0 else 3,
                    business_impact=5 if index == 0 else 3,
                ),
            )
            for index, use_case in enumerate(use_cases)
        ]
    )


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


def _final_report(final_selection: FinalSelectionOutput) -> FinalReport:
    return FinalReport(
        company_name="Acme Corporation",
        executive_summary="Top three use cases are ready for client discussion.",
        company_context="Acme is a manufacturing company focused on widgets.",
        methodology=(
            "Candidates were generated, scored once, and selected as the final "
            "top three."
        ),
        top_3_use_cases=[
            _final_report_use_case(item, rank)
            for rank, item in enumerate(final_selection.selected, start=1)
        ],
        caveats=["Validate data access before implementation."],
        source_urls=["https://example.com/company", "https://example.com/pain-1"],
    )


def _markdown_report() -> MarkdownReport:
    return MarkdownReport(
        markdown=(
            "# Acme Corporation GenAI Opportunity Report\n\n"
            "## Executive Summary\n\n"
            "Top three use cases are ready for client discussion."
        )
    )


@pytest.mark.asyncio
async def test_pipeline_runs_steps_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    company_research_query = ""
    company_profile_query = ""
    generation_pain_points: PainPointProfilerOutput | None = None
    grading_use_cases: list[list[GenAIUseCaseCandidate]] = []
    grading_company_profiles: list[CompanyProfileOutput] = []
    final_selection_candidates: GradedUseCasePool | None = None
    final_report_params: FinalReportInput | None = None
    markdown_report_params: MarkdownReportInput | None = None
    generated_candidates = _candidate_pool()
    graded_candidates = _graded_pool(generated_candidates.use_cases)
    final_selection = FinalSelectionOutput(
        selected=select_top_n(graded_candidates.graded_use_cases, 3)
    )
    final_report_result = _final_report(final_selection)
    markdown_report_result = _markdown_report()

    async def research_company_resolution(_params: object) -> ResearchResult:
        calls.append("research_company_resolution")
        return ResearchResult(text="resolution research")

    async def structure_company_resolution(_params: object) -> CompanyResolutionOutput:
        calls.append("structure_company_resolution")
        return _company_resolution()

    async def research_company(params: Any) -> ResearchResult:
        nonlocal company_research_query
        calls.append("research_company")
        company_research_query = params.company_query
        return ResearchResult(text="company research")

    async def structure_company_profile(params: Any) -> CompanyProfileOutput:
        nonlocal company_profile_query
        calls.append("structure_company_profile")
        company_profile_query = params.company_query
        return _company_profile()

    async def research_pain_points(_params: object) -> ResearchResult:
        calls.append("research_pain_points")
        return ResearchResult(text="pain research")

    async def structure_pain_points(_params: object) -> PainPointProfilerOutput:
        calls.append("structure_pain_points")
        return PainPointProfilerOutput(
            pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
        )

    async def generate_genai_use_cases(params: Any) -> GenAIUseCaseCandidatePool:
        nonlocal generation_pain_points
        calls.append("generate_genai_use_cases")
        generation_pain_points = params.pain_points
        return generated_candidates

    async def grade_use_cases(params: Any) -> GradedUseCasePool:
        calls.append("grade_use_cases")
        grading_use_cases.append(params.use_cases)
        grading_company_profiles.append(params.company_profile)
        return graded_candidates

    async def select_final_top_3(params: GradedUseCasePool) -> FinalSelectionOutput:
        nonlocal final_selection_candidates
        calls.append("select_final_top_3")
        final_selection_candidates = params
        return final_selection

    async def write_final_report(params: FinalReportInput) -> FinalReport:
        nonlocal final_report_params
        calls.append("write_final_report")
        final_report_params = params
        return final_report_result

    async def write_markdown_report(params: MarkdownReportInput) -> MarkdownReport:
        nonlocal markdown_report_params
        calls.append("write_markdown_report")
        markdown_report_params = params
        return markdown_report_result

    monkeypatch.setattr(
        pipeline, "research_company_resolution", research_company_resolution
    )
    monkeypatch.setattr(
        pipeline, "structure_company_resolution", structure_company_resolution
    )
    monkeypatch.setattr(pipeline, "research_company", research_company)
    monkeypatch.setattr(
        pipeline, "structure_company_profile", structure_company_profile
    )
    monkeypatch.setattr(pipeline, "research_pain_points", research_pain_points)
    monkeypatch.setattr(pipeline, "structure_pain_points", structure_pain_points)
    monkeypatch.setattr(pipeline, "generate_genai_use_cases", generate_genai_use_cases)
    monkeypatch.setattr(pipeline, "grade_use_cases", grade_use_cases)
    monkeypatch.setattr(pipeline, "select_final_top_3", select_final_top_3)
    monkeypatch.setattr(pipeline, "write_final_report", write_final_report)
    monkeypatch.setattr(pipeline, "write_markdown_report", write_markdown_report)

    result = await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == [
        "research_company_resolution",
        "structure_company_resolution",
        "research_company",
        "structure_company_profile",
        "research_pain_points",
        "structure_pain_points",
        "generate_genai_use_cases",
        "grade_use_cases",
        "select_final_top_3",
        "write_final_report",
        "write_markdown_report",
    ]
    assert [output.kind for output in result.outputs] == [
        "text",
        "json",
        "text",
        "json",
        "text",
        "json",
        "json",
        "json",
        "json",
        "json",
        "text",
    ]
    assert result.outputs[1].data == _company_resolution().model_dump(mode="json")
    assert result.outputs[6].data == generated_candidates.model_dump(mode="json")
    assert result.outputs[7].data == graded_candidates.model_dump(mode="json")
    assert result.outputs[8].data == {
        "final_top_3": final_selection.model_dump(mode="json")
    }
    assert result.outputs[9].data == {
        "final_report": final_report_result.model_dump(mode="json")
    }
    assert result.outputs[10].text == markdown_report_result.markdown
    assert generation_pain_points == PainPointProfilerOutput(
        pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
    )
    assert grading_use_cases == [generated_candidates.use_cases]
    assert grading_company_profiles == [_company_profile()]
    assert final_selection_candidates == graded_candidates
    assert final_report_params == FinalReportInput(
        company_profile=_company_profile(),
        pain_points=PainPointProfilerOutput(
            pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
        ),
        final_selection=final_selection,
    )
    assert markdown_report_params == MarkdownReportInput(
        final_report=final_report_result,
    )
    assert company_research_query == "Acme Corporation"
    assert company_profile_query == "Acme Corporation"
    assert result.final == markdown_report_result.markdown
    assert "Executive Summary" in result.final


@pytest.mark.asyncio
async def test_pipeline_stops_on_first_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def research_company_resolution(_params: object) -> ResearchResult:
        calls.append("research_company_resolution")
        return ResearchResult(text="resolution research")

    async def structure_company_resolution(_params: object) -> CompanyResolutionOutput:
        calls.append("structure_company_resolution")
        return _company_resolution()

    async def research_company(_params: object) -> ResearchResult:
        calls.append("research_company")
        return ResearchResult(text="company research")

    async def structure_company_profile(_params: object) -> CompanyProfileOutput:
        calls.append("structure_company_profile")
        raise RuntimeError("model failed")

    async def research_pain_points(_params: object) -> ResearchResult:
        calls.append("research_pain_points")
        return ResearchResult(text="should not run")

    monkeypatch.setattr(
        pipeline, "research_company_resolution", research_company_resolution
    )
    monkeypatch.setattr(
        pipeline, "structure_company_resolution", structure_company_resolution
    )
    monkeypatch.setattr(pipeline, "research_company", research_company)
    monkeypatch.setattr(
        pipeline, "structure_company_profile", structure_company_profile
    )
    monkeypatch.setattr(pipeline, "research_pain_points", research_pain_points)

    with pytest.raises(RuntimeError, match="model failed"):
        await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == [
        "research_company_resolution",
        "structure_company_resolution",
        "research_company",
        "structure_company_profile",
    ]


def test_compute_total_score_sums_rubric_dimensions() -> None:
    score = _score(
        "uc-1",
        company_relevance=5,
        business_impact=4,
        iconicness=3,
        genai_fit=2,
        feasibility=1,
        evidence_strength=5,
        total=6,
    )

    assert compute_total_score(score) == 20


def test_select_top_n_sorts_by_total_and_tie_breakers() -> None:
    graded = [
        GradedUseCase(
            use_case=_candidate(1),
            score=_score(
                "uc-1",
                company_relevance=3,
                business_impact=5,
                iconicness=5,
                genai_fit=3,
                feasibility=2,
                evidence_strength=2,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(2),
            score=_score(
                "uc-2",
                company_relevance=5,
                business_impact=1,
                iconicness=1,
                genai_fit=5,
                feasibility=4,
                evidence_strength=4,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(3),
            score=_score(
                "uc-3",
                company_relevance=5,
                business_impact=4,
                iconicness=1,
                genai_fit=4,
                feasibility=3,
                evidence_strength=3,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(4),
            score=_score(
                "uc-4",
                company_relevance=5,
                business_impact=4,
                iconicness=5,
                genai_fit=2,
                feasibility=2,
                evidence_strength=2,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(5),
            score=_score(
                "uc-5",
                company_relevance=4,
                business_impact=4,
                iconicness=4,
                genai_fit=3,
                feasibility=3,
                evidence_strength=3,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(6),
            score=_score(
                "uc-6",
                company_relevance=5,
                business_impact=5,
                iconicness=5,
                genai_fit=2,
                feasibility=1,
                evidence_strength=1,
            ),
        ),
    ]

    selected = select_top_n(graded, 5)

    assert [item.use_case.id for item in selected] == [
        "uc-5",
        "uc-4",
        "uc-3",
        "uc-2",
        "uc-1",
    ]
    assert len(selected) == 5


@pytest.mark.asyncio
async def test_use_case_grader_agent_recomputes_total_without_sorting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_cases = [_candidate(index) for index in range(1, 7)]
    llm_result = GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=use_cases[0],
                score=_score(
                    "uc-1",
                    company_relevance=2,
                    business_impact=2,
                    iconicness=2,
                    genai_fit=2,
                    feasibility=2,
                    evidence_strength=2,
                    total=30,
                ),
            ),
            GradedUseCase(
                use_case=use_cases[1],
                score=_score(
                    "uc-2",
                    company_relevance=5,
                    business_impact=4,
                    iconicness=4,
                    genai_fit=4,
                    feasibility=4,
                    evidence_strength=3,
                    total=6,
                ),
            ),
            *[
                GradedUseCase(
                    use_case=use_case,
                    score=_score(use_case.id),
                )
                for use_case in use_cases[2:]
            ],
        ]
    )

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> GradedUseCasePool:
        return llm_result

    monkeypatch.setattr(grader, "parse_chat_model", parse_chat_model)

    result = await UseCaseGraderAgent(client=object()).run(
        GradeUseCasesInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            use_cases=use_cases,
        )
    )

    assert [item.use_case.id for item in result.graded_use_cases[:2]] == [
        "uc-1",
        "uc-2",
    ]
    assert [item.score.total for item in result.graded_use_cases[:2]] == [12, 24]


@pytest.mark.asyncio
async def test_grade_use_cases_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_cases = [_candidate(index) for index in range(1, 7)]
    agent_result = _graded_pool(use_cases)

    class FakeUseCaseGraderAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(self, _params: GradeUseCasesInput) -> GradedUseCasePool:
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "UseCaseGraderAgent", FakeUseCaseGraderAgent)

    result = await activities.grade_use_cases(
        GradeUseCasesInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            use_cases=use_cases,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_final_reporter_agent_returns_structured_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = FinalSelectionOutput(
        selected=_graded_pool(_candidate_pool().use_cases).graded_use_cases[:3]
    )
    agent_result = _final_report(selected)

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> FinalReport:
        return agent_result

    monkeypatch.setattr(final_reporter, "parse_chat_model", parse_chat_model)

    result = await FinalReporterAgent(client=object()).run(
        FinalReportInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            final_selection=selected,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_final_reporter_agent_rejects_wrong_rank_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = FinalSelectionOutput(
        selected=_graded_pool(_candidate_pool().use_cases).graded_use_cases[:3]
    )
    agent_result = _final_report(selected)
    agent_result = agent_result.model_copy(
        update={
            "top_3_use_cases": [
                agent_result.top_3_use_cases[0],
                agent_result.top_3_use_cases[1].model_copy(update={"rank": 1}),
                agent_result.top_3_use_cases[2],
            ]
        }
    )

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> FinalReport:
        return agent_result

    monkeypatch.setattr(final_reporter, "parse_chat_model", parse_chat_model)

    with pytest.raises(RuntimeError, match="ranked 1, 2, and 3"):
        await FinalReporterAgent(client=object()).run(
            FinalReportInput(
                company_profile=_company_profile(),
                pain_points=PainPointProfilerOutput(
                    pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
                ),
                final_selection=selected,
            )
        )


@pytest.mark.asyncio
async def test_write_final_report_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = FinalSelectionOutput(
        selected=_graded_pool(_candidate_pool().use_cases).graded_use_cases[:3]
    )
    agent_result = _final_report(selected)

    class FakeFinalReporterAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(self, _params: FinalReportInput) -> FinalReport:
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "FinalReporterAgent", FakeFinalReporterAgent)

    result = await activities.write_final_report(
        FinalReportInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            final_selection=selected,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_markdown_reporter_agent_returns_markdown_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = FinalSelectionOutput(
        selected=_graded_pool(_candidate_pool().use_cases).graded_use_cases[:3]
    )
    final_report = _final_report(selected)
    agent_result = _markdown_report()
    model_name = ""

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> MarkdownReport:
        nonlocal model_name
        model_name = _kwargs["model"]
        return agent_result

    monkeypatch.setattr(
        markdown_reporter.settings,
        "MARKDOWN_REPORTER_AGENT_MODEL",
        "markdown-model",
    )
    monkeypatch.setattr(markdown_reporter, "parse_chat_model", parse_chat_model)

    result = await MarkdownReporterAgent(client=cast(Any, object())).run(
        MarkdownReportInput(final_report=final_report)
    )

    assert result == agent_result
    assert model_name == "markdown-model"


@pytest.mark.asyncio
async def test_write_markdown_report_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = FinalSelectionOutput(
        selected=_graded_pool(_candidate_pool().use_cases).graded_use_cases[:3]
    )
    final_report = _final_report(selected)
    agent_result = _markdown_report()

    class FakeMarkdownReporterAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(self, _params: MarkdownReportInput) -> MarkdownReport:
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "MarkdownReporterAgent", FakeMarkdownReporterAgent)

    result = await activities.write_markdown_report(
        MarkdownReportInput(final_report=final_report)
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_select_final_top_3_activity_returns_selection() -> None:
    pool = GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(
                    f"uc-{index}",
                    company_relevance=index,
                    business_impact=3,
                    iconicness=3,
                    genai_fit=3,
                    feasibility=3,
                    evidence_strength=3,
                ),
            )
            for index in range(1, 6)
        ]
    )

    result = await activities.select_final_top_3(pool)

    assert [item.use_case.id for item in result.selected] == [
        "uc-5",
        "uc-4",
        "uc-3",
    ]


def test_company_resolution_output_requires_llm_fields() -> None:
    with pytest.raises(ValidationError):
        CompanyResolutionOutput.model_validate({"input_name": "Acme"})


def test_company_resolution_output_forbids_extra_fields() -> None:
    data = _company_resolution().model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        CompanyResolutionOutput.model_validate(data)


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_company_resolution_output_bounds_confidence(confidence: float) -> None:
    data = _company_resolution().model_dump()
    data["confidence"] = confidence

    with pytest.raises(ValidationError):
        CompanyResolutionOutput.model_validate(data)


def test_company_resolution_output_requires_evidence() -> None:
    data = _company_resolution().model_dump()
    data["evidence"] = []

    with pytest.raises(ValidationError):
        CompanyResolutionOutput.model_validate(data)


def test_company_profile_output_requires_llm_fields() -> None:
    with pytest.raises(ValidationError):
        CompanyProfileOutput.model_validate({"company_name": "Acme"})


def test_company_profile_output_forbids_extra_fields() -> None:
    data = _company_profile().model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        CompanyProfileOutput.model_validate(data)


def test_pain_point_profiler_requires_at_least_three_points() -> None:
    with pytest.raises(ValidationError):
        PainPointProfilerOutput(
            pain_points=[_pain_point(1), _pain_point(2)],
        )


@pytest.mark.parametrize("count", [7, 13])
def test_genai_use_case_candidate_pool_requires_eight_to_twelve_items(
    count: int,
) -> None:
    with pytest.raises(ValidationError):
        GenAIUseCaseCandidatePool(
            use_cases=[_candidate(index) for index in range(1, count + 1)]
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "company_relevance",
        "business_impact",
        "iconicness",
        "genai_fit",
        "feasibility",
        "evidence_strength",
    ],
)
def test_use_case_score_bounds_rubric_fields(field_name: str) -> None:
    data = _score("uc-1").model_dump()
    data[field_name] = 6

    with pytest.raises(ValidationError):
        UseCaseScore.model_validate(data)


def test_graded_use_case_pool_allows_generated_pool_grading() -> None:
    pool = GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 9)
        ]
    )

    assert len(pool.graded_use_cases) == 8


def test_graded_use_case_pool_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        GradedUseCasePool(graded_use_cases=[])


@pytest.mark.parametrize("count", [2, 4])
def test_final_selection_output_requires_exactly_three_items(count: int) -> None:
    with pytest.raises(ValidationError):
        FinalSelectionOutput(
            selected=[
                GradedUseCase(
                    use_case=_candidate(index),
                    score=_score(f"uc-{index}"),
                )
                for index in range(1, count + 1)
            ],
        )


def test_final_selection_output_forbids_extra_fields() -> None:
    data = FinalSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 4)
        ],
    ).model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        FinalSelectionOutput.model_validate(data)


@pytest.mark.parametrize("count", [2, 4])
def test_final_report_requires_exactly_three_use_cases(count: int) -> None:
    selection = FinalSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 4)
        ]
    )
    data = _final_report(selection).model_dump()
    if count == 2:
        data["top_3_use_cases"] = data["top_3_use_cases"][:2]
    else:
        data["top_3_use_cases"].append(data["top_3_use_cases"][0])

    with pytest.raises(ValidationError):
        FinalReport.model_validate(data)


def test_final_report_forbids_extra_fields() -> None:
    selection = FinalSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 4)
        ]
    )
    data = _final_report(selection).model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        FinalReport.model_validate(data)


def test_final_report_use_case_requires_source_urls() -> None:
    selection = FinalSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 4)
        ]
    )
    data = _final_report(selection).top_3_use_cases[0].model_dump()
    data["source_urls"] = []

    with pytest.raises(ValidationError):
        FinalReportUseCase.model_validate(data)


def test_final_report_use_case_requires_allowed_rank() -> None:
    selection = FinalSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 4)
        ]
    )
    data = _final_report(selection).top_3_use_cases[0].model_dump()
    data["rank"] = 4

    with pytest.raises(ValidationError):
        FinalReportUseCase.model_validate(data)


def test_markdown_report_forbids_extra_fields() -> None:
    data = _markdown_report().model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        MarkdownReport.model_validate(data)


def test_workflow_result_final_is_markdown_string() -> None:
    result = SparkstralWorkflowResult(outputs=[], final=_markdown_report().markdown)

    assert result.final.startswith("# Acme Corporation")


@pytest.mark.parametrize(
    "field_name",
    ["target_users", "risks", "linked_pain_points", "evidence_sources"],
)
def test_genai_use_case_candidates_forbid_empty_required_lists(
    field_name: str,
) -> None:
    data = GenAIUseCaseCandidatePool(
        use_cases=[_candidate(index) for index in range(1, 9)]
    ).model_dump()
    data["use_cases"][0][field_name] = []

    with pytest.raises(ValidationError):
        GenAIUseCaseCandidatePool.model_validate(data)
