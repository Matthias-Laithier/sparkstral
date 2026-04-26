from datetime import timedelta

import mistralai.workflows as workflows

from src.agents.company_profiler import CompanyProfilerAgent
from src.agents.company_resolver import CompanyResolverAgent
from src.agents.final_reporter import FinalReporterAgent
from src.agents.genai_use_cases import GenAIUseCasesAgent
from src.agents.grader import UseCaseGraderAgent
from src.agents.markdown_reporter import MarkdownReporterAgent
from src.agents.pain_point_profiler import PainPointProfilerAgent
from src.agents.web_search import WebSearchAgent, WebSearchInput
from src.prompts import (
    company_research_prompt,
    company_resolution_research_prompt,
    pain_point_research_prompt,
)
from src.schemas import (
    CompanyProfileInput,
    CompanyProfileOutput,
    CompanyProfileStructuringInput,
    CompanyResolutionInput,
    CompanyResolutionOutput,
    CompanyResolutionStructuringInput,
    FinalReport,
    FinalReportInput,
    FinalSelectionOutput,
    GenAIUseCaseCandidateInput,
    GenAIUseCaseCandidatePool,
    GradedUseCasePool,
    GradeUseCasesInput,
    MarkdownReport,
    MarkdownReportInput,
    PainPointProfilerOutput,
    PainPointResearchInput,
    PainPointStructuringInput,
    ResearchResult,
)
from src.utils import get_mistral_client, select_top_n


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def research_company_resolution(params: CompanyResolutionInput) -> ResearchResult:
    client = get_mistral_client()
    agent = WebSearchAgent(client=client)
    try:
        result = await agent.run(
            WebSearchInput(
                prompt=company_resolution_research_prompt(params.company_query),
            )
        )
    except Exception as exc:
        raise RuntimeError("company resolution research failed") from exc
    return ResearchResult(text=result.text)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def structure_company_resolution(
    params: CompanyResolutionStructuringInput,
) -> CompanyResolutionOutput:
    client = get_mistral_client()
    agent = CompanyResolverAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("company resolution structuring failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def research_company(params: CompanyProfileInput) -> ResearchResult:
    client = get_mistral_client()
    agent = WebSearchAgent(client=client)
    try:
        result = await agent.run(
            WebSearchInput(prompt=company_research_prompt(params.company_query))
        )
    except Exception as exc:
        raise RuntimeError("company research failed") from exc
    return ResearchResult(text=result.text)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def structure_company_profile(
    params: CompanyProfileStructuringInput,
) -> CompanyProfileOutput:
    client = get_mistral_client()
    agent = CompanyProfilerAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("company profile structuring failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def research_pain_points(params: PainPointResearchInput) -> ResearchResult:
    client = get_mistral_client()
    agent = WebSearchAgent(client=client)
    try:
        result = await agent.run(
            WebSearchInput(
                prompt=pain_point_research_prompt(params.company_profile),
            )
        )
    except Exception as exc:
        raise RuntimeError("pain point research failed") from exc
    return ResearchResult(text=result.text)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def structure_pain_points(
    params: PainPointStructuringInput,
) -> PainPointProfilerOutput:
    client = get_mistral_client()
    agent = PainPointProfilerAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("pain point structuring failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def generate_genai_use_cases(
    params: GenAIUseCaseCandidateInput,
) -> GenAIUseCaseCandidatePool:
    client = get_mistral_client()
    agent = GenAIUseCasesAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("GenAI use-case generation failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def grade_use_cases(
    params: GradeUseCasesInput,
) -> GradedUseCasePool:
    client = get_mistral_client()
    agent = UseCaseGraderAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("use-case grading failed") from exc


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
async def write_final_report(params: FinalReportInput) -> FinalReport:
    client = get_mistral_client()
    agent = FinalReporterAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("final report writing failed") from exc


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def write_markdown_report(params: MarkdownReportInput) -> MarkdownReport:
    client = get_mistral_client()
    agent = MarkdownReporterAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("markdown report writing failed") from exc
