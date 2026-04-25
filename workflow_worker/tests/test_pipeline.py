import pytest

from src import pipeline
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    GenAIUseCaseItem,
    GenAIUseCasesOutput,
    PainPointItem,
    PainPointProfilerOutput,
    ResearchResult,
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

    async def research_company(_params: object) -> ResearchResult:
        calls.append("research_company")
        return ResearchResult(text="company research")

    async def structure_company_profile(_params: object) -> CompanyProfileOutput:
        calls.append("structure_company_profile")
        return CompanyProfileOutput(company_name="Acme")

    async def research_pain_points(_params: object) -> ResearchResult:
        calls.append("research_pain_points")
        return ResearchResult(text="pain research")

    async def structure_pain_points(_params: object) -> PainPointProfilerOutput:
        calls.append("structure_pain_points")
        return PainPointProfilerOutput(
            pain_points=[
                PainPointItem(
                    title="Pain",
                    description="Description",
                    prominence=8,
                    sources=["https://example.com"],
                )
            ]
        )

    async def generate_genai_use_cases(_params: object) -> GenAIUseCasesOutput:
        calls.append("generate_genai_use_cases")
        return GenAIUseCasesOutput(use_cases=[_use_case(1), _use_case(2), _use_case(3)])

    monkeypatch.setattr(pipeline, "research_company", research_company)
    monkeypatch.setattr(
        pipeline, "structure_company_profile", structure_company_profile
    )
    monkeypatch.setattr(pipeline, "research_pain_points", research_pain_points)
    monkeypatch.setattr(pipeline, "structure_pain_points", structure_pain_points)
    monkeypatch.setattr(pipeline, "generate_genai_use_cases", generate_genai_use_cases)

    result = await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == [
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
        "json",
    ]
    assert len(result.final.use_cases) == 3


@pytest.mark.asyncio
async def test_pipeline_stops_on_first_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def research_company(_params: object) -> ResearchResult:
        calls.append("research_company")
        return ResearchResult(text="company research")

    async def structure_company_profile(_params: object) -> CompanyProfileOutput:
        calls.append("structure_company_profile")
        raise RuntimeError("model failed")

    async def research_pain_points(_params: object) -> ResearchResult:
        calls.append("research_pain_points")
        return ResearchResult(text="should not run")

    monkeypatch.setattr(pipeline, "research_company", research_company)
    monkeypatch.setattr(
        pipeline, "structure_company_profile", structure_company_profile
    )
    monkeypatch.setattr(pipeline, "research_pain_points", research_pain_points)

    with pytest.raises(RuntimeError, match="model failed"):
        await pipeline.run_sparkstral_pipeline(CompanyInput(company_name="Acme"))

    assert calls == ["research_company", "structure_company_profile"]
