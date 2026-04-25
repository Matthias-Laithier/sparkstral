from datetime import timedelta

import mistralai.workflows as workflows

from src.agents.company_profiler import CompanyProfilerAgent
from src.agents.genai_use_cases import GenAIUseCasesAgent
from src.agents.pain_point_profiler import PainPointProfilerAgent
from src.agents.web_search import WebSearchAgent, WebSearchInput
from src.prompts import company_research_prompt, pain_point_research_prompt
from src.schemas import (
    CompanyProfileInput,
    CompanyProfileOutput,
    CompanyProfileStructuringInput,
    GenAIUseCasesInput,
    GenAIUseCasesOutput,
    PainPointProfilerOutput,
    PainPointResearchInput,
    PainPointStructuringInput,
    ResearchResult,
)
from src.utils import get_mistral_client


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
    params: GenAIUseCasesInput,
) -> GenAIUseCasesOutput:
    client = get_mistral_client()
    agent = GenAIUseCasesAgent(client=client)
    try:
        return await agent.run(params)
    except Exception as exc:
        raise RuntimeError("GenAI use-case generation failed") from exc
