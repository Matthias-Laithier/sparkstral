from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import company_profile_system_prompt, company_profile_user_prompt
from src.schemas import (
    CompanyProfileOutput,
    CompanyProfileStructuringInput,
)
from src.utils import parse_chat_model


class CompanyProfilerAgent(
    BaseAgent[CompanyProfileStructuringInput, CompanyProfileOutput]
):
    name = "company-profiler"

    async def run(self, params: CompanyProfileStructuringInput) -> CompanyProfileOutput:
        return await parse_chat_model(
            self.client,
            CompanyProfileOutput,
            phase="company profile structuring",
            model=settings.COMPANY_PROFILER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": company_profile_system_prompt()},
                {
                    "role": "user",
                    "content": company_profile_user_prompt(
                        params.company_query,
                        params.research_text,
                    ),
                },
            ],
        )
