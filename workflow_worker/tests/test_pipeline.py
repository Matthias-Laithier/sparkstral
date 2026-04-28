import pytest

from src.core.schemas import (
    CompanyInput,
    FinalSelectionOutput,
    GradedUseCasePool,
    GradeSingleUseCaseInput,
    IdeationBrief,
    IdeationInput,
    MarkdownReport,
    ResearchResult,
    SingleUseCaseGeneration,
    SingleUseCaseGradeResult,
    SingleUseCaseInput,
)
from src.pipeline import run_sparkstral_pipeline
from src.utils.selection import select_top_n

from . import factories as f


async def _noop(_msg: str) -> None:
    pass


@pytest.mark.asyncio
async def test_pipeline_runs_all_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    ideation = f.make_ideation_brief()
    graded_pool = GradedUseCasePool(
        grader_thinking="thinking",
        graded_use_cases=[f.make_graded(i) for i in range(1, 6)],
    )
    final = FinalSelectionOutput(selected=select_top_n(graded_pool.graded_use_cases, 3))
    report = MarkdownReport(markdown="# Report")

    async def mock_research(_p: object) -> ResearchResult:
        calls.append("research")
        return ResearchResult(text="research")

    async def mock_ideation(_p: IdeationInput) -> IdeationBrief:
        calls.append("ideation")
        return ideation

    async def mock_generate(p: SingleUseCaseInput) -> SingleUseCaseGeneration:
        calls.append("generate")
        return SingleUseCaseGeneration(
            use_case=f.make_candidate(p.use_case_index),
        )

    async def mock_grade(p: GradeSingleUseCaseInput) -> SingleUseCaseGradeResult:
        calls.append("grade")
        return f.make_grade_result(p.use_case.id)

    async def mock_select(_p: object) -> FinalSelectionOutput:
        calls.append("select")
        return final

    async def mock_report(_p: object) -> MarkdownReport:
        calls.append("report")
        return report

    import src.pipeline as pipeline

    monkeypatch.setattr(pipeline, "research_company", mock_research)
    monkeypatch.setattr(pipeline, "generate_ideation_brief", mock_ideation)
    monkeypatch.setattr(pipeline, "generate_single_use_case", mock_generate)
    monkeypatch.setattr(pipeline, "grade_single_use_case", mock_grade)
    monkeypatch.setattr(pipeline, "select_final_top_3", mock_select)
    monkeypatch.setattr(pipeline, "write_markdown_report", mock_report)

    result = await run_sparkstral_pipeline(CompanyInput(company_name="Acme"), _noop)

    assert calls[0] == "research"
    assert calls[1] == "ideation"
    assert calls.count("generate") == 5
    assert "grade" in calls
    assert calls[-2] == "select"
    assert calls[-1] == "report"
    assert result.final == "# Report"


@pytest.mark.asyncio
async def test_pipeline_stops_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def mock_research(_p: object) -> ResearchResult:
        calls.append("research")
        return ResearchResult(text="research")

    async def mock_ideation(_p: object) -> IdeationBrief:
        raise RuntimeError("ideation failed")

    import src.pipeline as pipeline

    monkeypatch.setattr(pipeline, "research_company", mock_research)
    monkeypatch.setattr(pipeline, "generate_ideation_brief", mock_ideation)

    with pytest.raises(RuntimeError, match="ideation failed"):
        await run_sparkstral_pipeline(CompanyInput(company_name="Acme"), _noop)

    assert calls == ["research"]
