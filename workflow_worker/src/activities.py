from datetime import date, timedelta
from typing import Any

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk, WebSearchTool

from src.agents.fact_checker import FactCheckAgent
from src.agents.genai_use_cases import SingleUseCaseAgent
from src.agents.grader import SingleUseCaseGraderAgent
from src.agents.ideation import IdeationAgent
from src.agents.markdown_reporter import MarkdownReporterAgent
from src.core.config import settings
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
from src.prompts.web_search import research_prompt, web_search_system_prompt
from src.tools.web_search import web_search
from src.utils.selection import select_top_n


@workflows.activity(start_to_close_timeout=timedelta(minutes=2))
async def search_web(query: str) -> str:
    """Search the web for current information about the given query.

    Args:
        query: The search query to look up.
    """
    return await web_search(query)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def research_company(params: ResearchInput) -> ResearchResult:
    tools: list[Any] = (
        [WebSearchTool()]
        if settings.WEB_SEARCH_PROVIDER == "mistralai"
        else [search_web]
    )

    session = workflows_mistralai.RemoteSession()
    agent = workflows_mistralai.Agent(
        model=settings.WEB_SEARCH_MODEL,
        name="research-agent",
        description="Researches companies via web search",
        instructions=web_search_system_prompt(date.today()),
        tools=tools,
    )

    outputs = await workflows_mistralai.Runner.run(
        agent=agent,
        inputs=research_prompt(params.company_query),
        session=session,
        max_turns=settings.WEB_SEARCH_MAX_ROUNDS,
    )

    text = "\n".join(output.text for output in outputs if isinstance(output, TextChunk))
    if not text.strip():
        raise RuntimeError("research produced no usable text")
    return ResearchResult(text=text)


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
