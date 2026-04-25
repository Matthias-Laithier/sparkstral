from typing import Any

import pytest
from pydantic import ValidationError

from src import activities, pipeline
from src.agents import grader, red_team, refiner
from src.agents.grader import UseCaseGraderAgent, compute_total_score
from src.agents.red_team import RedTeamAgent
from src.agents.refiner import UseCaseRefinerAgent
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    CompanyResolutionOutput,
    DeduplicatedUseCasePool,
    EvidenceItem,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidatePool,
    GradedUseCase,
    GradedUseCasePool,
    GradeUseCasesInput,
    InitialSelectionOutput,
    OpportunityItem,
    OpportunityMapOutput,
    PainPointItem,
    PainPointProfilerOutput,
    RedTeamInput,
    RedTeamOutput,
    RedTeamReview,
    RefinedUseCase,
    RefinedUseCasePool,
    RefineUseCasesInput,
    ResearchResult,
    UseCaseCriticism,
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


def _candidate(index: int) -> GenAIUseCaseCandidate:
    opportunity_index = ((index - 1) % 3) + 1
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
        linked_opportunities=[f"Opportunity {opportunity_index}"],
        evidence_sources=[f"https://example.com/pain-{opportunity_index}"],
        ideation_lens=IDEATION_LENSES[(index - 1) % len(IDEATION_LENSES)],
    )


def _candidate_pool() -> GenAIUseCaseCandidatePool:
    return GenAIUseCaseCandidatePool(
        use_cases=[_candidate(index) for index in range(1, 9)]
    )


def _deduplicated_pool() -> DeduplicatedUseCasePool:
    return DeduplicatedUseCasePool(
        use_cases=[_candidate(index) for index in range(1, 7)],
        removed_or_merged=["uc-7 merged into uc-2", "uc-8 removed as duplicate"],
        rationale=(
            "Merged overlapping candidates and kept the most company-specific set."
        ),
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


def _criticism(index: int = 1) -> UseCaseCriticism:
    return UseCaseCriticism(
        title=f"Weakness {index}",
        comment="The claim is not sufficiently supported by the provided evidence.",
        severity="medium",
        required_fix="Add evidence that directly supports the claimed impact.",
    )


def _red_team_review(use_case_id: str, index: int = 1) -> RedTeamReview:
    return RedTeamReview(
        use_case_id=use_case_id,
        criticisms=[_criticism(index)],
        verdict="revise",
    )


def _red_team_output(selected_use_cases: list[GradedUseCase]) -> RedTeamOutput:
    return RedTeamOutput(
        reviews=[
            _red_team_review(item.use_case.id, index)
            for index, item in enumerate(selected_use_cases, start=1)
        ]
    )


def _refined_use_case(item: GradedUseCase, index: int = 1) -> RefinedUseCase:
    return RefinedUseCase(
        original_use_case_id=item.use_case.id,
        refined_use_case=item.use_case.model_copy(
            update={
                "title": f"Refined {item.use_case.title}",
                "why_this_company": "Sharper company-specific fit",
                "expected_impact": "More concrete operational impact",
            }
        ),
        changes_made=[f"Addressed red-team weakness {index}"],
        unresolved_concerns=[f"Concern {index} still needs validation"],
    )


def _refined_pool(selected_use_cases: list[GradedUseCase]) -> RefinedUseCasePool:
    return RefinedUseCasePool(
        refined_use_cases=[
            _refined_use_case(item, index)
            for index, item in enumerate(selected_use_cases, start=1)
        ]
    )


@pytest.mark.asyncio
async def test_pipeline_runs_steps_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    company_research_query = ""
    company_profile_query = ""
    generation_opportunity_map: OpportunityMapOutput | None = None
    deduplication_candidates: GenAIUseCaseCandidatePool | None = None
    grading_use_cases: list[list[GenAIUseCaseCandidate]] = []
    grading_company_profiles: list[CompanyProfileOutput] = []
    selection_candidates: GradedUseCasePool | None = None
    final_selection_candidates: GradedUseCasePool | None = None
    red_team_params: RedTeamInput | None = None
    refiner_params: RefineUseCasesInput | None = None
    generated_candidates = _candidate_pool()
    deduplicated_candidates = _deduplicated_pool()
    graded_candidates = _graded_pool(deduplicated_candidates.use_cases)
    initial_selection = InitialSelectionOutput(
        selected=graded_candidates.graded_use_cases[:5],
    )
    red_team_result = _red_team_output(initial_selection.selected)
    refined_result = _refined_pool(initial_selection.selected)
    refined_candidates = [
        item.refined_use_case for item in refined_result.refined_use_cases
    ]
    final_graded_candidates = GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=refined_candidates[0],
                score=_score(refined_candidates[0].id),
            ),
            GradedUseCase(
                use_case=refined_candidates[1],
                score=_score(
                    refined_candidates[1].id,
                    company_relevance=5,
                    business_impact=5,
                ),
            ),
            GradedUseCase(
                use_case=refined_candidates[2],
                score=_score(
                    refined_candidates[2].id,
                    company_relevance=5,
                    business_impact=5,
                    iconicness=5,
                    genai_fit=5,
                    feasibility=5,
                    evidence_strength=5,
                ),
            ),
            GradedUseCase(
                use_case=refined_candidates[3],
                score=_score(
                    refined_candidates[3].id,
                    company_relevance=5,
                    business_impact=5,
                    iconicness=5,
                    genai_fit=4,
                    feasibility=4,
                    evidence_strength=4,
                ),
            ),
            GradedUseCase(
                use_case=refined_candidates[4],
                score=_score(
                    refined_candidates[4].id,
                    company_relevance=5,
                    business_impact=5,
                    iconicness=4,
                    genai_fit=4,
                    feasibility=4,
                    evidence_strength=4,
                ),
            ),
        ]
    )
    final_selection = FinalSelectionOutput(
        selected=select_top_n(final_graded_candidates.graded_use_cases, 3)
    )

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

    async def map_opportunities(_params: object) -> OpportunityMapOutput:
        calls.append("map_opportunities")
        return _opportunity_map()

    async def generate_genai_use_cases(params: Any) -> GenAIUseCaseCandidatePool:
        nonlocal generation_opportunity_map
        calls.append("generate_genai_use_cases")
        generation_opportunity_map = params.opportunity_map
        return generated_candidates

    async def deduplicate_use_cases(params: Any) -> DeduplicatedUseCasePool:
        nonlocal deduplication_candidates
        calls.append("deduplicate_use_cases")
        deduplication_candidates = params.candidates
        return deduplicated_candidates

    async def grade_use_cases(params: Any) -> GradedUseCasePool:
        calls.append("grade_use_cases")
        grading_use_cases.append(params.use_cases)
        grading_company_profiles.append(params.company_profile)
        if len(grading_use_cases) == 1:
            return graded_candidates
        return final_graded_candidates

    async def select_initial_top_5(
        params: GradedUseCasePool,
    ) -> InitialSelectionOutput:
        nonlocal selection_candidates
        calls.append("select_initial_top_5")
        selection_candidates = params
        return initial_selection

    async def select_final_top_3(params: GradedUseCasePool) -> FinalSelectionOutput:
        nonlocal final_selection_candidates
        calls.append("select_final_top_3")
        final_selection_candidates = params
        return final_selection

    async def red_team_use_cases(params: RedTeamInput) -> RedTeamOutput:
        nonlocal red_team_params
        calls.append("red_team_use_cases")
        red_team_params = params
        return red_team_result

    async def refine_use_cases(params: RefineUseCasesInput) -> RefinedUseCasePool:
        nonlocal refiner_params
        calls.append("refine_use_cases")
        refiner_params = params
        return refined_result

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
    monkeypatch.setattr(pipeline, "map_opportunities", map_opportunities)
    monkeypatch.setattr(pipeline, "generate_genai_use_cases", generate_genai_use_cases)
    monkeypatch.setattr(pipeline, "deduplicate_use_cases", deduplicate_use_cases)
    monkeypatch.setattr(pipeline, "grade_use_cases", grade_use_cases)
    monkeypatch.setattr(pipeline, "select_initial_top_5", select_initial_top_5)
    monkeypatch.setattr(pipeline, "select_final_top_3", select_final_top_3)
    monkeypatch.setattr(pipeline, "red_team_use_cases", red_team_use_cases)
    monkeypatch.setattr(pipeline, "refine_use_cases", refine_use_cases)

    result = await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == [
        "research_company_resolution",
        "structure_company_resolution",
        "research_company",
        "structure_company_profile",
        "research_pain_points",
        "structure_pain_points",
        "map_opportunities",
        "generate_genai_use_cases",
        "deduplicate_use_cases",
        "grade_use_cases",
        "select_initial_top_5",
        "red_team_use_cases",
        "refine_use_cases",
        "grade_use_cases",
        "select_final_top_3",
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
        "json",
        "json",
        "json",
        "json",
        "json",
    ]
    assert result.outputs[1].data == _company_resolution().model_dump(mode="json")
    assert result.outputs[6].data == _opportunity_map().model_dump(mode="json")
    assert result.outputs[7].data == generated_candidates.model_dump(mode="json")
    assert result.outputs[8].data == deduplicated_candidates.model_dump(mode="json")
    assert result.outputs[9].data == graded_candidates.model_dump(mode="json")
    assert result.outputs[10].data == {
        "initial_top_5": initial_selection.model_dump(mode="json")
    }
    assert result.outputs[11].data == {
        "red_team_review": red_team_result.model_dump(mode="json")
    }
    assert result.outputs[12].data == {
        "refined_use_cases": refined_result.model_dump(mode="json")
    }
    assert result.outputs[13].data == {
        "final_grading": final_graded_candidates.model_dump(mode="json")
    }
    assert result.outputs[14].data == {
        "final_top_3": final_selection.model_dump(mode="json")
    }
    assert generation_opportunity_map == _opportunity_map()
    assert deduplication_candidates == generated_candidates
    assert grading_use_cases == [deduplicated_candidates.use_cases, refined_candidates]
    assert grading_company_profiles == [_company_profile(), _company_profile()]
    assert selection_candidates == graded_candidates
    assert final_selection_candidates == final_graded_candidates
    assert red_team_params == RedTeamInput(
        company_profile=_company_profile(),
        pain_points=PainPointProfilerOutput(
            pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
        ),
        opportunity_map=_opportunity_map(),
        selected_use_cases=initial_selection.selected,
    )
    assert refiner_params == RefineUseCasesInput(
        company_profile=_company_profile(),
        pain_points=PainPointProfilerOutput(
            pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
        ),
        opportunity_map=_opportunity_map(),
        selected_use_cases=initial_selection.selected,
        red_team=red_team_result,
    )
    assert company_research_query == "Acme Corporation"
    assert company_profile_query == "Acme Corporation"
    assert result.final == final_selection
    assert len(result.final.selected) == 3
    assert [item.use_case.id for item in result.final.selected] == [
        "uc-3",
        "uc-4",
        "uc-5",
    ]
    assert all(
        item.use_case.title.startswith("Refined ") for item in result.final.selected
    )


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
            opportunity_map=_opportunity_map(),
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
            opportunity_map=_opportunity_map(),
            use_cases=use_cases,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_red_team_agent_returns_structured_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    agent_result = _red_team_output(selected)

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> RedTeamOutput:
        return agent_result

    monkeypatch.setattr(red_team, "parse_chat_model", parse_chat_model)

    result = await RedTeamAgent(client=object()).run(
        RedTeamInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            opportunity_map=_opportunity_map(),
            selected_use_cases=selected,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_red_team_agent_rejects_missing_selected_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    agent_result = RedTeamOutput(
        reviews=[
            _red_team_review(item.use_case.id, index)
            for index, item in enumerate(selected[:4], start=1)
        ]
        + [_red_team_review("uc-other", 5)]
    )

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> RedTeamOutput:
        return agent_result

    monkeypatch.setattr(red_team, "parse_chat_model", parse_chat_model)

    with pytest.raises(
        RuntimeError,
        match="exactly one review per selected use case",
    ):
        await RedTeamAgent(client=object()).run(
            RedTeamInput(
                company_profile=_company_profile(),
                pain_points=PainPointProfilerOutput(
                    pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
                ),
                opportunity_map=_opportunity_map(),
                selected_use_cases=selected,
            )
        )


@pytest.mark.asyncio
async def test_red_team_use_cases_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    agent_result = _red_team_output(selected)

    class FakeRedTeamAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(self, _params: RedTeamInput) -> RedTeamOutput:
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "RedTeamAgent", FakeRedTeamAgent)

    result = await activities.red_team_use_cases(
        RedTeamInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            opportunity_map=_opportunity_map(),
            selected_use_cases=selected,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_refiner_agent_returns_structured_refinements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    red_team_result = _red_team_output(selected)
    agent_result = _refined_pool(selected)

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> RefinedUseCasePool:
        return agent_result

    monkeypatch.setattr(refiner, "parse_chat_model", parse_chat_model)

    result = await UseCaseRefinerAgent(client=object()).run(
        RefineUseCasesInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            opportunity_map=_opportunity_map(),
            selected_use_cases=selected,
            red_team=red_team_result,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_refiner_agent_rejects_missing_selected_refinement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    red_team_result = _red_team_output(selected)
    agent_result = RefinedUseCasePool(
        refined_use_cases=[
            _refined_use_case(item, index)
            for index, item in enumerate(selected[:4], start=1)
        ]
        + [
            RefinedUseCase(
                original_use_case_id="uc-other",
                refined_use_case=_candidate(6),
                changes_made=["Changed unsupported details"],
                unresolved_concerns=["Original candidate was not selected"],
            )
        ]
    )

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> RefinedUseCasePool:
        return agent_result

    monkeypatch.setattr(refiner, "parse_chat_model", parse_chat_model)

    with pytest.raises(
        RuntimeError,
        match="exactly one item per selected use case",
    ):
        await UseCaseRefinerAgent(client=object()).run(
            RefineUseCasesInput(
                company_profile=_company_profile(),
                pain_points=PainPointProfilerOutput(
                    pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
                ),
                opportunity_map=_opportunity_map(),
                selected_use_cases=selected,
                red_team=red_team_result,
            )
        )


@pytest.mark.asyncio
async def test_refiner_agent_rejects_missing_original_evidence_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    red_team_result = _red_team_output(selected)
    first_refined = _refined_use_case(selected[0])
    first_refined = first_refined.model_copy(
        update={
            "refined_use_case": first_refined.refined_use_case.model_copy(
                update={"evidence_sources": ["https://example.com/new-source"]}
            )
        }
    )
    agent_result = RefinedUseCasePool(
        refined_use_cases=[first_refined]
        + [
            _refined_use_case(item, index)
            for index, item in enumerate(selected[1:], start=2)
        ]
    )

    async def parse_chat_model(*_args: Any, **_kwargs: Any) -> RefinedUseCasePool:
        return agent_result

    monkeypatch.setattr(refiner, "parse_chat_model", parse_chat_model)

    with pytest.raises(
        RuntimeError,
        match="preserve original evidence source URLs",
    ):
        await UseCaseRefinerAgent(client=object()).run(
            RefineUseCasesInput(
                company_profile=_company_profile(),
                pain_points=PainPointProfilerOutput(
                    pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
                ),
                opportunity_map=_opportunity_map(),
                selected_use_cases=selected,
                red_team=red_team_result,
            )
        )


@pytest.mark.asyncio
async def test_refine_use_cases_activity_returns_agent_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    red_team_result = _red_team_output(selected)
    agent_result = _refined_pool(selected)

    class FakeUseCaseRefinerAgent:
        def __init__(self, client: object) -> None:
            self.client = client

        async def run(self, _params: RefineUseCasesInput) -> RefinedUseCasePool:
            return agent_result

    monkeypatch.setattr(activities, "get_mistral_client", lambda: object())
    monkeypatch.setattr(activities, "UseCaseRefinerAgent", FakeUseCaseRefinerAgent)

    result = await activities.refine_use_cases(
        RefineUseCasesInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            opportunity_map=_opportunity_map(),
            selected_use_cases=selected,
            red_team=red_team_result,
        )
    )

    assert result == agent_result


@pytest.mark.asyncio
async def test_select_initial_top_5_activity_returns_selection() -> None:
    pool = GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(
                    f"uc-{index}",
                    company_relevance=index if index <= 5 else 1,
                    business_impact=3,
                    iconicness=3,
                    genai_fit=3,
                    feasibility=3,
                    evidence_strength=3,
                ),
            )
            for index in range(1, 7)
        ]
    )

    result = await activities.select_initial_top_5(pool)

    assert [item.use_case.id for item in result.selected] == [
        "uc-5",
        "uc-4",
        "uc-3",
        "uc-2",
        "uc-1",
    ]


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


def test_opportunity_map_requires_at_least_three_opportunities() -> None:
    with pytest.raises(ValidationError):
        OpportunityMapOutput(
            opportunities=[_opportunity(1), _opportunity(2)],
            summary="Too few opportunities",
        )


@pytest.mark.parametrize(
    "field_name",
    ["linked_pain_points", "likely_data_sources", "evidence_sources"],
)
def test_opportunity_map_forbids_empty_required_lists(field_name: str) -> None:
    data = OpportunityMapOutput(
        opportunities=[_opportunity(1), _opportunity(2), _opportunity(3)],
        summary="Opportunity summary",
    ).model_dump()
    data["opportunities"][0][field_name] = []

    with pytest.raises(ValidationError):
        OpportunityMapOutput.model_validate(data)


@pytest.mark.parametrize("count", [7, 13])
def test_genai_use_case_candidate_pool_requires_eight_to_twelve_items(
    count: int,
) -> None:
    with pytest.raises(ValidationError):
        GenAIUseCaseCandidatePool(
            use_cases=[_candidate(index) for index in range(1, count + 1)]
        )


@pytest.mark.parametrize("count", [5, 11])
def test_deduplicated_use_case_pool_requires_six_to_ten_items(
    count: int,
) -> None:
    with pytest.raises(ValidationError):
        DeduplicatedUseCasePool(
            use_cases=[_candidate(index) for index in range(1, count + 1)],
            removed_or_merged=["Merged overlapping candidates"],
            rationale="Deduplicated the candidate pool.",
        )


def test_deduplicated_use_case_pool_requires_merge_explanation() -> None:
    data = _deduplicated_pool().model_dump()
    del data["removed_or_merged"]

    with pytest.raises(ValidationError):
        DeduplicatedUseCasePool.model_validate(data)


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


def test_graded_use_case_pool_allows_refined_top_five_grading() -> None:
    pool = GradedUseCasePool(
        graded_use_cases=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 6)
        ]
    )

    assert len(pool.graded_use_cases) == 5


def test_graded_use_case_pool_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        GradedUseCasePool(graded_use_cases=[])


@pytest.mark.parametrize("count", [4, 6])
def test_initial_selection_output_requires_exactly_five_items(count: int) -> None:
    with pytest.raises(ValidationError):
        InitialSelectionOutput(
            selected=[
                GradedUseCase(
                    use_case=_candidate(index),
                    score=_score(f"uc-{index}"),
                )
                for index in range(1, count + 1)
            ],
        )


def test_initial_selection_output_forbids_extra_fields() -> None:
    data = InitialSelectionOutput(
        selected=[
            GradedUseCase(
                use_case=_candidate(index),
                score=_score(f"uc-{index}"),
            )
            for index in range(1, 6)
        ],
    ).model_dump()
    data["unexpected"] = "ignored before strict schemas"

    with pytest.raises(ValidationError):
        InitialSelectionOutput.model_validate(data)


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


@pytest.mark.parametrize("count", [4, 6])
def test_red_team_input_requires_exactly_five_selected_use_cases(count: int) -> None:
    with pytest.raises(ValidationError):
        RedTeamInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            opportunity_map=_opportunity_map(),
            selected_use_cases=[
                GradedUseCase(
                    use_case=_candidate(index),
                    score=_score(f"uc-{index}"),
                )
                for index in range(1, count + 1)
            ],
        )


@pytest.mark.parametrize("count", [4, 6])
def test_red_team_output_requires_exactly_five_reviews(count: int) -> None:
    with pytest.raises(ValidationError):
        RedTeamOutput(
            reviews=[
                _red_team_review(f"uc-{index}", index) for index in range(1, count + 1)
            ]
        )


@pytest.mark.parametrize("count", [4, 6])
def test_refine_use_cases_input_requires_exactly_five_selected_use_cases(
    count: int,
) -> None:
    valid_selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]
    selected = [
        GradedUseCase(
            use_case=_candidate(index),
            score=_score(f"uc-{index}"),
        )
        for index in range(1, count + 1)
    ]
    with pytest.raises(ValidationError):
        RefineUseCasesInput(
            company_profile=_company_profile(),
            pain_points=PainPointProfilerOutput(
                pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
            ),
            opportunity_map=_opportunity_map(),
            selected_use_cases=selected,
            red_team=_red_team_output(valid_selected),
        )


@pytest.mark.parametrize("count", [4, 6])
def test_refined_use_case_pool_requires_exactly_five_items(count: int) -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[:5]

    with pytest.raises(ValidationError):
        RefinedUseCasePool(
            refined_use_cases=[
                _refined_use_case(selected[(index - 1) % 5], index)
                for index in range(1, count + 1)
            ]
        )


def test_refined_use_case_requires_changes_made() -> None:
    selected = _graded_pool(_deduplicated_pool().use_cases).graded_use_cases[0]

    with pytest.raises(ValidationError):
        RefinedUseCase(
            original_use_case_id=selected.use_case.id,
            refined_use_case=selected.use_case,
            changes_made=[],
            unresolved_concerns=[],
        )


def test_red_team_review_requires_criticism() -> None:
    with pytest.raises(ValidationError):
        RedTeamReview(
            use_case_id="uc-1",
            criticisms=[],
            verdict="revise",
        )


def test_red_team_criticism_requires_allowed_severity() -> None:
    data = _criticism().model_dump()
    data["severity"] = "critical"

    with pytest.raises(ValidationError):
        UseCaseCriticism.model_validate(data)


def test_red_team_review_requires_allowed_verdict() -> None:
    data = _red_team_review("uc-1").model_dump()
    data["verdict"] = "maybe"

    with pytest.raises(ValidationError):
        RedTeamReview.model_validate(data)


@pytest.mark.parametrize(
    "field_name",
    ["target_users", "risks", "linked_opportunities", "evidence_sources"],
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
