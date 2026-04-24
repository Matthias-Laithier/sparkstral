import mistralai.workflows as workflows
from mistralai.client import Mistral

from src.core.config import settings
from src.workflow.agents.company_profiler import CompanyProfilerAgent
from src.workflow.agents.genai_use_cases import GenAIUseCasesAgent
from src.workflow.agents.pain_point_profiler import PainPointProfilerAgent
from src.workflow.schemas import (
    CompanyProfileInput,
    CompanyProfilerResult,
    GenAIUseCasesInput,
    GenAIUseCasesOutput,
    PainPointProfilerInput,
    PainPointProfilerResult,
)


@workflows.activity()
async def profile_company(params: CompanyProfileInput) -> CompanyProfilerResult:
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    agent = CompanyProfilerAgent(client=client)
    return await agent.run(params)


@workflows.activity()
async def profile_pain_points(
    params: PainPointProfilerInput,
) -> PainPointProfilerResult:
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    agent = PainPointProfilerAgent(client=client)
    return await agent.run(params)


@workflows.activity()
async def generate_genai_use_cases(
    params: GenAIUseCasesInput,
) -> GenAIUseCasesOutput:
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    agent = GenAIUseCasesAgent(client=client)
    return await agent.run(params)
