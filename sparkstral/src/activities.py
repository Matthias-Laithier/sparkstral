from datetime import timedelta

import mistralai.workflows as workflows

from src.agents.fact_checker import FactCheckAgent
from src.agents.genai_use_cases import SingleUseCaseAgent
from src.agents.grader import SingleUseCaseGraderAgent
from src.agents.ideation import IdeationAgent
from src.agents.markdown_reporter import MarkdownReporterAgent
from src.agents.researcher import ResearchAgent
from src.core.schemas import (
    FactCheckInput,
    FactCheckOutput,
    FinalSelectionOutput,
    GradedUseCasePool,
    GradeSingleUseCaseInput,
    IdeationBrief,
    IdeationInput,
    MarkdownReport,
    MarkdownReportInput,
    ResearchInput,
    ResearchResult,
    SingleUseCaseGeneration,
    SingleUseCaseGradeResult,
    SingleUseCaseInput,
)
from src.llm import get_mistral_client
from src.utils.selection import select_top_n


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def research_company(params: ResearchInput) -> ResearchResult:
    agent = ResearchAgent()
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("company research failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=2))
async def generate_ideation_brief(params: IdeationInput) -> IdeationBrief:
    client = get_mistral_client()
    agent = IdeationAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("ideation brief generation failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=3))
async def generate_single_use_case(
    params: SingleUseCaseInput,
) -> SingleUseCaseGeneration:
    client = get_mistral_client()
    agent = SingleUseCaseAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError(
            f"use-case generation failed for uc_{params.use_case_index}"
        ) from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=2))
async def fact_check_use_case(params: FactCheckInput) -> FactCheckOutput:
    client = get_mistral_client()
    agent = FactCheckAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError(f"fact-check failed for {params.use_case.id}") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def grade_single_use_case(
    params: GradeSingleUseCaseInput,
) -> SingleUseCaseGradeResult:
    client = get_mistral_client()
    agent = SingleUseCaseGraderAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError(f"use-case grading failed for {params.use_case.id}") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def select_final_top_3(
    params: GradedUseCasePool,
) -> FinalSelectionOutput:
    try:
        selected = select_top_n(params.graded_use_cases, 3)
        if len(selected) != 3:
            raise RuntimeError("final top-3 selection produced fewer than 3 use cases")
        return FinalSelectionOutput(selected=selected)
    except Exception as exc:
        raise RuntimeError("final top-3 selection failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def write_markdown_report(params: MarkdownReportInput) -> MarkdownReport:
    client = get_mistral_client()
    agent = MarkdownReporterAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("markdown report writing failed") from exc
