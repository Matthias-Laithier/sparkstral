from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import (
    company_resolution_system_prompt,
    company_resolution_user_prompt,
)
from src.schemas import (
    CompanyResolutionOutput,
    CompanyResolutionStructuringInput,
)
from src.utils import parse_chat_model


class CompanyResolverAgent(
    BaseAgent[CompanyResolutionStructuringInput, CompanyResolutionOutput]
):
    name = "company-resolver"

    async def run(
        self,
        params: CompanyResolutionStructuringInput,
    ) -> CompanyResolutionOutput:
        return await parse_chat_model(
            self.client,
            CompanyResolutionOutput,
            phase="company resolution structuring",
            model=settings.COMPANY_RESOLVER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": company_resolution_system_prompt()},
                {
                    "role": "user",
                    "content": company_resolution_user_prompt(
                        params.company_query,
                        params.research_text,
                    ),
                },
            ],
        )
