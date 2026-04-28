from datetime import timedelta

import mistralai.workflows as workflows

from src.agents.genai_use_cases import GenAIUseCasesAgent
from src.agents.grader import SingleUseCaseGraderAgent
from src.agents.markdown_reporter import MarkdownReporterAgent
from src.agents.web_search import WebSearchAgent, WebSearchInput
from src.prompts import combined_research_prompt
from src.schemas import (
    CompanyResolutionInput,
    FinalSelectionOutput,
    GenAIUseCaseCandidateInput,
    GenAIUseCaseGeneration,
    GradedUseCasePool,
    GradeSingleUseCaseInput,
    MarkdownReport,
    MarkdownReportInput,
    ResearchResult,
    SingleUseCaseGradeResult,
)
from src.utils import get_mistral_client, select_top_n


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def research_company(params: CompanyResolutionInput) -> ResearchResult:
    client = get_mistral_client()
    agent = WebSearchAgent(client=client)
    try:
        result = await agent.run(
            WebSearchInput(
                prompt=combined_research_prompt(params.company_query),
            )
        )
    except Exception as exc:
        raise RuntimeError("combined company research failed") from exc
    return ResearchResult(text=result.text)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def generate_genai_use_cases(
    params: GenAIUseCaseCandidateInput,
) -> GenAIUseCaseGeneration:
    client = get_mistral_client()
    agent = GenAIUseCasesAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("GenAI use-case generation failed") from exc


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
