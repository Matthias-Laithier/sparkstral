import mistralai.workflows as workflows
from mistralai.client import Mistral

from src.core.config import settings
from src.workflow.agents.company_profiler import CompanyProfilerAgent
from src.workflow.schemas import CompanyProfileInput, CompanyProfileOutput


@workflows.activity()
async def profile_company(params: CompanyProfileInput) -> CompanyProfileOutput:
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    agent = CompanyProfilerAgent(client=client)
    return await agent.run(params)
