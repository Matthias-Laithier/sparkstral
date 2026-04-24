from datetime import timedelta

import mistralai.workflows as workflows

from src.agents.company_profiler import CompanyProfilerAgent
from src.agents.genai_use_cases import GenAIUseCasesAgent
from src.agents.pain_point_profiler import PainPointProfilerAgent
from src.schemas import (
    CompanyProfileInput,
    CompanyProfilerResult,
    GenAIUseCasesInput,
    GenAIUseCasesOutput,
    PainPointProfilerInput,
    PainPointProfilerResult,
)
from src.utils import get_mistral_client


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def profile_company(params: CompanyProfileInput) -> CompanyProfilerResult:
    client = get_mistral_client()
    agent = CompanyProfilerAgent(client=client)
    return await agent.run(params)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def profile_pain_points(
    params: PainPointProfilerInput,
) -> PainPointProfilerResult:
    client = get_mistral_client()
    agent = PainPointProfilerAgent(client=client)
    return await agent.run(params)


@workflows.activity(start_to_close_timeout=timedelta(minutes=5))
async def generate_genai_use_cases(
    params: GenAIUseCasesInput,
) -> GenAIUseCasesOutput:
    client = get_mistral_client()
    agent = GenAIUseCasesAgent(client=client)
    return await agent.run(params)
