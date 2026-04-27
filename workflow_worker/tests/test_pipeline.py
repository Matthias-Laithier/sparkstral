from typing import Any, cast

import pytest
from pydantic import ValidationError

from src import activities, pipeline
from src.agents import genai_use_cases, grader, markdown_reporter
from src.agents.genai_use_cases import GenAIUseCasesAgent
from src.agents.grader import (
    SingleUseCaseGraderAgent,
    build_graded_use_case_pool,
    build_single_use_case_grade_inputs,
    compute_weighted_total,
)
from src.agents.markdown_reporter import MarkdownReporterAgent
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    CompanyResolutionOutput,
    DimensionRubricLine,
    EvidenceItem,
    FinalSelectionOutput,
    GenAIMechanism,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidateInput,
    GenAIUseCaseCandidatePool,
    GenAIUseCaseGeneration,
    GradedUseCase,
    GradedUseCasePool,
    GradeSingleUseCaseInput,
    MarkdownReport,
    MarkdownReportInput,
    PilotKPI,
    ResearchResult,
    SingleUseCaseGradeResult,
    SourceBackedMetric,
    SparkstralWorkflowResult,
    UseCaseGrade,
    UseCaseScore,
)
from src.utils import select_top_n


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
        company_resolution=_company_resolution(),
        research_text=(
            "**Business Lines & Customer Segments**\n"
            "- Claim: Acme makes widgets.\n"
            "  Source URL: https://example.com/products\n"
            "  Citation: Products page describes Acme's widget business.\n"
            "- Claim: Acme serves industrial buyers.\n"
            "  Source URL: https://example.com/customers\n"
            "  Citation: Customer page names industrial buyers.\n\n"
            "**Operational Pain Points & Opportunities**\n"
            "- Claim: Acme faces supply chain delays.\n"
            "  Source URL: https://example.com/pain-1\n"
            "  Citation: Annual report notes supply chain delays.\n"
            "- Claim: New safety rules affect Acme's plants.\n"
            "  Source URL: https://example.com/pain-2\n"
            "  Citation: Regulator page describes new safety rules.\n"
            "- Claim: Customers expect faster configuration support.\n"
            "  Source URL: https://example.com/pain-3\n"
            "  Citation: Industry publication reports faster configuration "
            "expectations.\n"
            "- Claim: Acme has an aftermarket service expansion opportunity.\n"
            "  Source URL: https://example.com/growth\n"
            "  Citation: Investor presentation highlights aftermarket service "
            "expansion."
        ),
    )


def _genai_mechanism() -> GenAIMechanism:
    return GenAIMechanism(
        mechanisms=["document_understanding", "structured_generation"],
        why_genai_is_needed="The workflow needs document reasoning and generation.",
        genai_advantage_over_classical_software=(
            "Rule-based systems can cover routing, while GenAI adds document "
            "reasoning over messy operational context."
        ),
        genai_advantage_over_classical_ml=(
            "Classical ML can rank known patterns, while GenAI drafts grounded "
            "recommendations with explanations."
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


def _candidate(
    index: int, *, business_domain: str = "manufacturing"
) -> GenAIUseCaseCandidate:
    pain_point_index = ((index - 1) % 3) + 1
    evidence_source = f"https://example.com/pain-{pain_point_index}"
    return GenAIUseCaseCandidate(
        id=f"uc_{index}",
        title=f"Use case {index}",
        business_domain=business_domain,
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
        company_signal_labels=[f"signal_{index}", "supply_chain_pressure"],
        evidence_sources=[evidence_source],
    )


def _candidate_pool() -> GenAIUseCaseCandidatePool:
    return GenAIUseCaseCandidatePool(
        use_cases=[_candidate(index) for index in range(1, 6)]
    )


def _genai_use_case_generation(count: int = 5) -> GenAIUseCaseGeneration:
    return GenAIUseCaseGeneration(
        ideation_brief=(
            "Cover agentic tools, OCR on documents, RAG with citations, and "
            "multimodal; reject generic KPI-only ideas."
        ),
        use_cases=[_candidate(index) for index in range(1, count + 1)],
    )


def _line(score: int, label: str) -> DimensionRubricLine:
    return DimensionRubricLine(
        rationale=f"Rationale for {label}.",
        score=score,
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
    weighted_total: float | None = None,
    penalties: list[str] | None = None,
) -> UseCaseScore:
    computed_weighted_total = round(
        0.25 * iconicness
        + 0.25 * genai_fit
        + 0.20 * business_impact
        + 0.15 * company_relevance
        + 0.08 * feasibility
        + 0.07 * evidence_strength,
        2,
    )
    return UseCaseScore(
        use_case_id=use_case_id,
        strengths=["Strength"],
        weaknesses=["Weakness"],
        rationale="Rationale",
        company_relevance=_line(company_relevance, "company_relevance"),
        business_impact=_line(business_impact, "business_impact"),
        iconicness=_line(iconicness, "iconicness"),
        genai_fit=_line(genai_fit, "genai_fit"),
        feasibility=_line(feasibility, "feasibility"),
        evidence_strength=_line(evidence_strength, "evidence_strength"),
        penalties=[] if penalties is None else penalties,
        weighted_total=(
            computed_weighted_total if weighted_total is None else weighted_total
        ),
    )


def _grade(
    use_case_id: str,
    *,
    company_relevance: int = 3,
    business_impact: int = 3,
    iconicness: int = 3,
    genai_fit: int = 3,
    feasibility: int = 3,
    evidence_strength: int = 3,
    penalties: list[str] | None = None,
) -> UseCaseGrade:
    score = _score(
        use_case_id,
        company_relevance=company_relevance,
        business_impact=business_impact,
        iconicness=iconicness,
        genai_fit=genai_fit,
        feasibility=feasibility,
        evidence_strength=evidence_strength,
        penalties=penalties,
    )
    return UseCaseGrade.model_validate(score.model_dump(exclude={"weighted_total"}))


def _graded_pool(use_cases: list[GenAIUseCaseCandidate]) -> GradedUseCasePool:
    return GradedUseCasePool(
        grader_thinking="Skeptical: classical alternatives noted before scoring.",
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
        ],
    )


def _markdown_report() -> MarkdownReport:
    return MarkdownReport(
        markdown=(
            "# GenAI Opportunity Report — Acme Corporation\n\n"
            "## Company Context\n\n"
            "Top three use cases are ready for client discussion."
        )
    )


@pytest.mark.asyncio
async def test_pipeline_runs_steps_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    generation_inputs: list[GenAIUseCaseCandidateInput] = []
    grading_inputs: list[GradeSingleUseCaseInput] = []
    grading_company_profiles: list[CompanyProfileOutput] = []
    final_selection_candidates: GradedUseCasePool | None = None
    markdown_report_params: MarkdownReportInput | None = None
    generated = _genai_use_case_generation(5)
    graded_candidates = _graded_pool(generated.use_cases)
    final_selection = FinalSelectionOutput(
        selected=select_top_n(graded_candidates.graded_use_cases, 3)
    )
    markdown_report_result = _markdown_report()
    expected_company_profile = CompanyProfileOutput(
        company_resolution=_company_resolution(),
        research_text="combined research",
    )

    async def research_company_combined(_params: object) -> ResearchResult:
        calls.append("research_company_combined")
        return ResearchResult(text="combined research")

    async def structure_company_resolution(_params: object) -> CompanyResolutionOutput:
        calls.append("structure_company_resolution")
        return _company_resolution()

    async def generate_genai_use_cases(
        params: GenAIUseCaseCandidateInput,
    ) -> GenAIUseCaseGeneration:
        calls.append("generate_genai_use_cases")
        generation_inputs.append(params)
        return generated

    async def grade_single_use_case(
        params: GradeSingleUseCaseInput,
    ) -> SingleUseCaseGradeResult:
        calls.append(f"grade_single_use_case:{params.use_case.id}")
        grading_inputs.append(params)
        grading_company_profiles.append(params.company_profile)
        score = next(
            item.score
            for item in graded_candidates.graded_use_cases
            if item.use_case.id == params.use_case.id
        )
        return SingleUseCaseGradeResult(
            grader_thinking=f"Standalone thinking for {params.use_case.id}.",
            grade=UseCaseGrade.model_validate(
                score.model_dump(exclude={"weighted_total"})
            ),
        )

    async def select_final_top_3(params: GradedUseCasePool) -> FinalSelectionOutput:
        nonlocal final_selection_candidates
        calls.append("select_final_top_3")
        final_selection_candidates = params
        return final_selection

    async def write_markdown_report(params: MarkdownReportInput) -> MarkdownReport:
        nonlocal markdown_report_params
        calls.append("write_markdown_report")
        markdown_report_params = params
        return markdown_report_result

    monkeypatch.setattr(
        pipeline, "research_company_combined", research_company_combined
    )
    monkeypatch.setattr(
        pipeline, "structure_company_resolution", structure_company_resolution
    )
    monkeypatch.setattr(pipeline, "generate_genai_use_cases", generate_genai_use_cases)
    monkeypatch.setattr(pipeline, "grade_single_use_case", grade_single_use_case)
    monkeypatch.setattr(pipeline, "select_final_top_3", select_final_top_3)
    monkeypatch.setattr(pipeline, "write_markdown_report", write_markdown_report)

    status_messages: list[str] = []

    async def status_callback(message: str) -> None:
        status_messages.append(message)

    result = await pipeline.run_sparkstral_pipeline(
        CompanyInput(company_name="Acme"),
        status_callback=status_callback,
    )

    assert calls == [
        "research_company_combined",
        "structure_company_resolution",
        "generate_genai_use_cases",
        "grade_single_use_case:uc_1",
        "grade_single_use_case:uc_2",
        "grade_single_use_case:uc_3",
        "grade_single_use_case:uc_4",
        "grade_single_use_case:uc_5",
        "select_final_top_3",
        "write_markdown_report",
    ]
    assert status_messages == [
        "Researching company context...\n",
        "Generating candidate use cases...\n",
        "Scoring opportunities...\n",
        "Writing final report...\n",
    ]
    assert [output.kind for output in result.outputs] == [
        "text",
        "json",
        "json",
        "json",
        "json",
        "text",
    ]
    assert result.outputs[1].data == _company_resolution().model_dump(mode="json")
    assert result.outputs[2].data == generated.model_dump(mode="json")
    assert final_selection_candidates is not None
    assert result.outputs[3].data == final_selection_candidates.model_dump(mode="json")
    assert [
        item.score.weighted_total
        for item in final_selection_candidates.graded_use_cases
    ] == [item.score.weighted_total for item in graded_candidates.graded_use_cases]
    assert "Standalone thinking for uc_1" in final_selection_candidates.grader_thinking
    assert result.outputs[4].data == {
        "final_top_3": final_selection.model_dump(mode="json")
    }
    assert result.outputs[5].text == markdown_report_result.markdown
    assert generation_inputs == [
        GenAIUseCaseCandidateInput(company_profile=expected_company_profile)
    ]
    assert [item.use_case for item in grading_inputs] == generated.use_cases
    assert [
        summary for summary in grading_inputs[0].peer_summaries if "uc_1:" in summary
    ] == []
    assert "uc_2: Use case 2" in grading_inputs[0].peer_summaries[0]
    assert grading_company_profiles == [expected_company_profile] * 5
    assert markdown_report_params == MarkdownReportInput(
        company_profile=expected_company_profile,
        final_selection=final_selection,
    )
    assert result.final == markdown_report_result.markdown


@pytest.mark.asyncio
async def test_pipeline_stops_on_first_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def research_company_combined(_params: object) -> ResearchResult:
        calls.append("research_company_combined")
        return ResearchResult(text="combined research")

    async def structure_company_resolution(_params: object) -> CompanyResolutionOutput:
        calls.append("structure_company_resolution")
        return _company_resolution()

    async def generate_genai_use_cases(
        _params: object,
    ) -> GenAIUseCaseGeneration:
        calls.append("generate_genai_use_cases")
        raise RuntimeError("model failed")

    monkeypatch.setattr(
        pipeline, "research_company_combined", research_company_combined
    )
    monkeypatch.setattr(
        pipeline, "structure_company_resolution", structure_company_resolution
    )
    monkeypatch.setattr(pipeline, "generate_genai_use_cases", generate_genai_use_cases)

    with pytest.raises(RuntimeError, match="model failed"):
        await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == [
        "research_company_combined",
        "structure_company_resolution",
        "generate_genai_use_cases",
    ]


def test_compute_weighted_total_uses_weighted_formula() -> None:
    score = _score(
        "uc_1",
        company_relevance=10,
        business_impact=8,
        iconicness=6,
        genai_fit=4,
        feasibility=2,
        evidence_strength=10,
    )

    assert compute_weighted_total(score) == 6.46


def test_build_single_use_case_grade_inputs_adds_peer_summaries() -> None:
    company_profile = _company_profile()
    use_cases = [_candidate(1), _candidate(2), _candidate(3)]

    grade_inputs = build_single_use_case_grade_inputs(company_profile, use_cases)

    assert [item.use_case for item in grade_inputs] == use_cases
    assert [item.company_profile for item in grade_inputs] == [company_profile] * 3
    assert "uc_1:" not in "\n".join(grade_inputs[0].peer_summaries)
    assert "uc_2: Use case 2" in grade_inputs[0].peer_summaries[0]
    assert "uc_3: Use case 3" in grade_inputs[0].peer_summaries[1]


def test_build_single_use_case_grade_inputs_rejects_duplicate_ids() -> None:
    use_cases = [_candidate(1), _candidate(1)]

    with pytest.raises(ValueError, match="duplicate IDs"):
        build_single_use_case_grade_inputs(_company_profile(), use_cases)


def test_build_graded_use_case_pool_applies_weighted_scores() -> None:
    use_cases = [_candidate(1), _candidate(2)]
    single_grades = [
        SingleUseCaseGradeResult(
            grader_thinking="Thinking one.",
            grade=_grade(
                "uc_1",
                company_relevance=5,
                business_impact=4,
                iconicness=4,
                genai_fit=4,
                feasibility=4,
                evidence_strength=3,
            ),
        ),
        SingleUseCaseGradeResult(
            grader_thinking="Thinking two.",
            grade=_grade("uc_2"),
        ),
    ]

    pool = build_graded_use_case_pool(use_cases, single_grades)

    assert pool.grader_thinking == "uc_1: Thinking one.\nuc_2: Thinking two."
    assert [item.use_case for item in pool.graded_use_cases] == use_cases
    assert [item.score.weighted_total for item in pool.graded_use_cases] == [4.08, 3.0]


def test_build_graded_use_case_pool_rejects_mismatched_grade_ids() -> None:
    with pytest.raises(ValueError, match="returned use case ID uc_missing for uc_1"):
        build_graded_use_case_pool(
            [_candidate(1)],
            [
                SingleUseCaseGradeResult(
                    grader_thinking="Mismatch.",
                    grade=_grade("uc_missing"),
                )
            ],
        )


def test_select_top_n_sorts_by_weighted_total_and_tie_breakers() -> None:
    graded = [
        GradedUseCase(
            use_case=_candidate(1),
            score=_score(
                "uc_1",
                company_relevance=10,
                business_impact=10,
                iconicness=8,
                genai_fit=8,
                feasibility=8,
                evidence_strength=8,
                weighted_total=8.0,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(2),
            score=_score(
                "uc_2",
                company_relevance=5,
                business_impact=1,
                iconicness=10,
                genai_fit=5,
                feasibility=5,
                evidence_strength=5,
                weighted_total=8.0,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(3),
            score=_score(
                "uc_3",
                company_relevance=10,
                business_impact=10,
                iconicness=9,
                genai_fit=8,
                feasibility=8,
                evidence_strength=8,
                weighted_total=8.0,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(4),
            score=_score(
                "uc_4",
                company_relevance=8,
                business_impact=10,
                iconicness=9,
                genai_fit=8,
                feasibility=8,
                evidence_strength=8,
                weighted_total=8.0,
            ),
        ),
        GradedUseCase(
            use_case=_candidate(5),
            score=_score(
                "uc_5",
                company_relevance=10,
                business_impact=10,
                iconicness=10,
                genai_fit=10,
                feasibility=10,
                evidence_strength=10,
                weighted_total=7.0,
            ),
        ),
    ]

    selected = select_top_n(graded, 5)

    assert [item.use_case.id for item in selected] == [
        "uc_3",
        "uc_4",
        "uc_1",
        "uc_2",
        "uc_5",
    ]
    assert len(selected) == 5


@pytest.mark.asyncio
async def test_genai_use_cases_agent_returns_generation_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent_result = _genai_use_case_generation(5)
    response_model: type[Any] | None = None
    model_name = ""
    phase = ""
    messages: list[dict[str, str]] = []

    async def parse_chat_model(
        *args: Any,
        **kwargs: Any,
    ) -> GenAIUseCaseGeneration:
        nonlocal response_model, model_name, phase, messages
        response_model = args[1]
        model_name = kwargs["model"]
        phase = kwargs["phase"]
        messages = kwargs["messages"]
        return agent_result

    monkeypatch.setattr(
        cast(Any, genai_use_cases).settings,
        "GENAI_USE_CASES_MODEL",
        "generation-model",
    )
    monkeypatch.setattr(genai_use_cases, "parse_chat_model", parse_chat_model)

    result = await GenAIUseCasesAgent(client=cast(Any, object())).run(
        GenAIUseCaseCandidateInput(company_profile=_company_profile())
    )

    assert result == agent_result
    assert response_model is GenAIUseCaseGeneration
    assert model_name == "generation-model"
    assert phase == "GenAI use-case generation"
    assert "uc_1" in messages[1]["content"] or "5" in messages[1]["content"]


@pytest.mark.asyncio
async def test_generate_genai_use_cases_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_params: list[GenAIUseCaseCandidateInput] = []
    batch = _genai_use_case_generation(5)

    class FakeGenAIUseCasesAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(
            self,
            params: GenAIUseCaseCandidateInput,
        ) -> GenAIUseCaseGeneration:
            captured_params.append(params)
            return batch

    generation_input = GenAIUseCaseCandidateInput(company_profile=_company_profile())

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "GenAIUseCasesAgent", FakeGenAIUseCasesAgent)

    result = await activities.generate_genai_use_cases(generation_input)

    assert result == batch
    assert captured_params == [generation_input]


@pytest.mark.asyncio
async def test_single_use_case_grader_agent_returns_single_grade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_case = _candidate(2)
    llm_result = SingleUseCaseGradeResult(
        grader_thinking="Classical software could address thin chat patterns.",
        grade=_grade(
            "uc_2",
            company_relevance=5,
            business_impact=4,
            iconicness=4,
            genai_fit=4,
            feasibility=4,
            evidence_strength=3,
        ),
    )
    response_model: type[Any] | None = None
    messages: list[dict[str, str]] = []

    async def parse_chat_model(
        *args: Any,
        **kwargs: Any,
    ) -> SingleUseCaseGradeResult:
        nonlocal response_model, messages
        response_model = args[1]
        messages = kwargs["messages"]
        return llm_result

    monkeypatch.setattr(grader, "parse_chat_model", parse_chat_model)

    result = await SingleUseCaseGraderAgent(client=cast(Any, object())).run(
        GradeSingleUseCaseInput(
            company_profile=_company_profile(),
            use_case=use_case,
            peer_summaries=["uc_1: Use case 1 — Problem"],
        )
    )

    assert result == llm_result
    assert response_model is SingleUseCaseGradeResult
    assert "Generated use case to grade" in messages[1]["content"]
    assert "uc_1: Use case 1" in messages[1]["content"]


@pytest.mark.asyncio
async def test_single_use_case_grader_agent_rejects_mismatched_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_result = SingleUseCaseGradeResult(
        grader_thinking="Mismatch.",
        grade=_grade("uc_missing"),
    )

    async def parse_chat_model(
        *_args: Any,
        **_kwargs: Any,
    ) -> SingleUseCaseGradeResult:
        return llm_result

    monkeypatch.setattr(grader, "parse_chat_model", parse_chat_model)

    with pytest.raises(ValueError, match="grader returned use case ID uc_missing"):
        await SingleUseCaseGraderAgent(client=cast(Any, object())).run(
            GradeSingleUseCaseInput(
                company_profile=_company_profile(),
                use_case=_candidate(1),
                peer_summaries=[],
            )
        )


@pytest.mark.asyncio
async def test_grade_single_use_case_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_case = _candidate(1)
    grading_input = GradeSingleUseCaseInput(
        company_profile=_company_profile(),
        use_case=use_case,
        peer_summaries=["uc_2: Use case 2 — Problem"],
    )
    agent_result = SingleUseCaseGradeResult(
        grader_thinking="Standalone thinking.",
        grade=_grade(use_case.id),
    )

    class FakeSingleUseCaseGraderAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(
            self,
            params: GradeSingleUseCaseInput,
        ) -> SingleUseCaseGradeResult:
            assert params == grading_input
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(
        activities,
        "SingleUseCaseGraderAgent",
        FakeSingleUseCaseGraderAgent,
    )

    result = await activities.grade_single_use_case(grading_input)

    assert result == agent_result


@pytest.mark.asyncio
async def test_markdown_reporter_agent_returns_markdown_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = FinalSelectionOutput(
        selected=_graded_pool(_candidate_pool().use_cases).graded_use_cases[:3]
    )
    agent_result = _markdown_report()
    model_name = ""

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> MarkdownReport:
        nonlocal model_name
        model_name = _kwargs["model"]
        return agent_result

    monkeypatch.setattr(
        cast(Any, markdown_reporter).settings,
        "MARKDOWN_REPORTER_AGENT_MODEL",
        "markdown-model",
    )
    monkeypatch.setattr(markdown_reporter, "parse_chat_model", parse_chat_model)

    result = await MarkdownReporterAgent(client=cast(Any, object())).run(
        MarkdownReportInput(
            company_profile=_company_profile(),
            final_selection=selected,
        )
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
    agent_result = _markdown_report()

    class FakeMarkdownReporterAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(self, _params: MarkdownReportInput) -> MarkdownReport:
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "MarkdownReporterAgent", FakeMarkdownReporterAgent)

    result = await activities.write_markdown_report(
        MarkdownReportInput(
            company_profile=_company_profile(),
            final_selection=selected,
        )
    )

    assert result == agent_result


def test_select_top_n_returns_top_three_by_score() -> None:
    graded = [
        GradedUseCase(
            use_case=_candidate(index),
            score=_score(f"uc_{index}", weighted_total=5.0 - index / 10),
        )
        for index in range(1, 5)
    ]

    selected = select_top_n(graded, 3)

    assert [item.use_case.id for item in selected] == [
        "uc_1",
        "uc_2",
        "uc_3",
    ]
    assert len(selected) == 3


def test_select_top_n_skips_same_domain() -> None:
    domains = ["domain_a", "domain_a", "domain_a", "domain_b", "domain_c"]
    graded = [
        GradedUseCase(
            use_case=_candidate(index, business_domain=domains[index - 1]),
            score=_score(f"uc_{index}", weighted_total=8.0 - index / 10),
        )
        for index in range(1, 6)
    ]

    selected = select_top_n(graded, 3)

    assert [item.use_case.id for item in selected] == [
        "uc_1",
        "uc_4",
        "uc_5",
    ]
    selected_domains = [item.use_case.business_domain for item in selected]
    assert len(set(selected_domains)) == 3


@pytest.mark.asyncio
async def test_select_final_top_3_activity_returns_selection() -> None:
    pool = GradedUseCasePool(
        grader_thinking="Ordered by weighted score.",
        graded_use_cases=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(
                    f"uc_{index}",
                    company_relevance=index,
                    business_impact=3,
                    iconicness=3,
                    genai_fit=3,
                    feasibility=3,
                    evidence_strength=3,
                ),
            )
            for index in range(1, 6)
        ],
    )

    result = await activities.select_final_top_3(pool)

    assert [item.use_case.id for item in result.selected] == [
        "uc_5",
        "uc_4",
        "uc_3",
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


def test_company_profile_output_requires_resolution_and_research_text() -> None:
    with pytest.raises(ValidationError):
        CompanyProfileOutput.model_validate({"company_name": "Acme"})


def test_company_profile_output_forbids_extra_fields() -> None:
    data = _company_profile().model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        CompanyProfileOutput.model_validate(data)


def test_company_profile_output_requires_research_text() -> None:
    data = _company_profile().model_dump()
    del data["research_text"]

    with pytest.raises(ValidationError):
        CompanyProfileOutput.model_validate(data)


@pytest.mark.parametrize("count", [4, 6])
def test_genai_use_case_candidate_pool_requires_exactly_five(count: int) -> None:
    with pytest.raises(ValidationError):
        GenAIUseCaseCandidatePool(
            use_cases=[_candidate(index) for index in range(1, count + 1)]
        )


def test_genai_use_case_generation_accepts_five() -> None:
    GenAIUseCaseGeneration(
        ideation_brief="Plan pillars then five ideas.",
        use_cases=[_candidate(index) for index in range(1, 6)],
    )


def test_genai_use_case_candidate_requires_genai_mechanism() -> None:
    data = _candidate(1).model_dump()
    del data["genai_mechanism"]

    with pytest.raises(ValidationError):
        GenAIUseCaseCandidate.model_validate(data)


def test_genai_use_case_candidate_allows_empty_source_backed_metrics() -> None:
    data = _candidate(1).model_dump()
    data["source_backed_metrics"] = []

    candidate = GenAIUseCaseCandidate.model_validate(data)

    assert candidate.source_backed_metrics == []


def test_genai_use_case_candidate_requires_two_pilot_kpis() -> None:
    data = _candidate(1).model_dump()
    data["pilot_kpis"] = data["pilot_kpis"][:1]

    with pytest.raises(ValidationError):
        GenAIUseCaseCandidate.model_validate(data)


def test_genai_use_case_candidate_requires_metric_source_in_evidence() -> None:
    data = _candidate(1).model_dump()
    data["source_backed_metrics"][0]["source_url"] = "https://example.com/other"

    with pytest.raises(ValidationError):
        GenAIUseCaseCandidate.model_validate(data)


def test_genai_use_case_candidate_has_no_archetype_field() -> None:
    data = _candidate(1).model_dump()
    assert "use_case_archetype" not in data


def test_source_backed_metric_forbids_extra_fields() -> None:
    data = _source_backed_metric("https://example.com/pain-1").model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        SourceBackedMetric.model_validate(data)


def test_pilot_kpi_restricts_target_direction() -> None:
    data = _pilot_kpis()[0].model_dump()
    data["target_direction"] = "double"

    with pytest.raises(ValidationError):
        PilotKPI.model_validate(data)


def test_genai_mechanism_requires_at_least_one_mechanism() -> None:
    data = _genai_mechanism().model_dump()
    data["mechanisms"] = []

    with pytest.raises(ValidationError):
        GenAIMechanism.model_validate(data)


def test_genai_mechanism_restricts_mechanism_values() -> None:
    data = _genai_mechanism().model_dump()
    data["mechanisms"] = ["predictive_maintenance"]

    with pytest.raises(ValidationError):
        GenAIMechanism.model_validate(data)


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
    data = _score("uc_1").model_dump()
    line = dict(data[field_name])
    line["score"] = 11
    data[field_name] = line

    with pytest.raises(ValidationError):
        UseCaseScore.model_validate(data)


def test_use_case_grade_forbids_weighted_total() -> None:
    data = _grade("uc_1").model_dump()
    data["weighted_total"] = 3.0

    with pytest.raises(ValidationError):
        UseCaseGrade.model_validate(data)


def test_single_use_case_grade_result_requires_grade() -> None:
    with pytest.raises(ValidationError):
        SingleUseCaseGradeResult(grader_thinking="x")


def test_graded_use_case_pool_allows_generated_pool_grading() -> None:
    pool = GradedUseCasePool(
        grader_thinking="Test grader preface.",
        graded_use_cases=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc_{index}"),
            )
            for index in range(1, 9)
        ],
    )

    assert len(pool.graded_use_cases) == 8


def test_graded_use_case_pool_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        GradedUseCasePool(grader_thinking="x", graded_use_cases=[])


@pytest.mark.parametrize("count", [2, 4])
def test_final_selection_output_requires_exactly_three_items(count: int) -> None:
    with pytest.raises(ValidationError):
        FinalSelectionOutput(
            selected=[
                GradedUseCase(
                    use_case=_candidate(index),
                    score=_score(f"uc_{index}"),
                )
                for index in range(1, count + 1)
            ],
        )


def test_final_selection_output_forbids_extra_fields() -> None:
    data = FinalSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc_{index}"),
            )
            for index in range(1, 4)
        ],
    ).model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        FinalSelectionOutput.model_validate(data)


def test_markdown_report_forbids_extra_fields() -> None:
    data = _markdown_report().model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        MarkdownReport.model_validate(data)


def test_workflow_result_final_is_markdown_string() -> None:
    result = SparkstralWorkflowResult(outputs=[], final=_markdown_report().markdown)

    assert result.final.startswith("# GenAI Opportunity Report — Acme Corporation")


@pytest.mark.parametrize(
    "field_name",
    ["target_users", "risks", "company_signal_labels", "evidence_sources"],
)
def test_genai_use_case_candidates_forbid_empty_required_lists(
    field_name: str,
) -> None:
    data = GenAIUseCaseCandidatePool(
        use_cases=[_candidate(index) for index in range(1, 6)]
    ).model_dump()
    data["use_cases"][0][field_name] = []

    with pytest.raises(ValidationError):
        GenAIUseCaseCandidatePool.model_validate(data)
