from typing import Any

import pytest
from pydantic import ValidationError

from src import pipeline
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    CompanyResolutionOutput,
    DeduplicatedUseCasePool,
    EvidenceItem,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidatePool,
    OpportunityItem,
    OpportunityMapOutput,
    PainPointItem,
    PainPointProfilerOutput,
    ResearchResult,
)

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


@pytest.mark.asyncio
async def test_pipeline_runs_steps_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    company_research_query = ""
    company_profile_query = ""
    generation_opportunity_map: OpportunityMapOutput | None = None
    deduplication_candidates: GenAIUseCaseCandidatePool | None = None
    generated_candidates = _candidate_pool()
    deduplicated_candidates = _deduplicated_pool()

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
    ]
    assert result.outputs[1].data == _company_resolution().model_dump(mode="json")
    assert result.outputs[6].data == _opportunity_map().model_dump(mode="json")
    assert result.outputs[7].data == deduplicated_candidates.model_dump(mode="json")
    assert generation_opportunity_map == _opportunity_map()
    assert deduplication_candidates == generated_candidates
    assert company_research_query == "Acme Corporation"
    assert company_profile_query == "Acme Corporation"
    assert result.final == deduplicated_candidates
    assert len(result.final.use_cases) == 6
    assert result.final.removed_or_merged
    assert result.final.rationale
    assert all(candidate.id for candidate in result.final.use_cases)
    assert all(candidate.ideation_lens for candidate in result.final.use_cases)
    assert all(candidate.linked_opportunities for candidate in result.final.use_cases)
    assert all(candidate.evidence_sources for candidate in result.final.use_cases)


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
