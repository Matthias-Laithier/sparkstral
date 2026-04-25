from typing import Any

import pytest
from pydantic import ValidationError

from src import pipeline
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    CompanyResolutionOutput,
    EvidenceItem,
    GenAIUseCaseItem,
    GenAIUseCasesOutput,
    PainPointItem,
    PainPointProfilerOutput,
    ResearchResult,
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


def _use_case(index: int) -> GenAIUseCaseItem:
    return GenAIUseCaseItem(
        title=f"Use case {index}",
        target_users=["Ops"],
        business_problem="Problem",
        why_this_company="Company fit",
        genai_solution="Solution",
        required_data="Data",
        expected_impact="Impact",
        risks=["Risk"],
    )


@pytest.mark.asyncio
async def test_pipeline_runs_steps_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    company_research_query = ""
    company_profile_query = ""

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

    async def generate_genai_use_cases(_params: object) -> GenAIUseCasesOutput:
        calls.append("generate_genai_use_cases")
        return GenAIUseCasesOutput(use_cases=[_use_case(1), _use_case(2), _use_case(3)])

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

    result = await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == [
        "research_company_resolution",
        "structure_company_resolution",
        "research_company",
        "structure_company_profile",
        "research_pain_points",
        "structure_pain_points",
        "generate_genai_use_cases",
    ]
    assert [output.kind for output in result.outputs] == [
        "text",
        "json",
        "text",
        "json",
        "text",
        "json",
        "json",
    ]
    assert result.outputs[1].data == _company_resolution().model_dump(mode="json")
    assert company_research_query == "Acme Corporation"
    assert company_profile_query == "Acme Corporation"
    assert len(result.final.use_cases) == 3


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


@pytest.mark.parametrize("count", [2, 4])
def test_genai_use_cases_output_requires_exactly_three_items(count: int) -> None:
    with pytest.raises(ValidationError):
        GenAIUseCasesOutput(use_cases=[_use_case(index) for index in range(count)])
