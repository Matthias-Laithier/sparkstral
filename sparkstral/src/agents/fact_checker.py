from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.schemas import FactCheckInput, FactCheckOutput
from src.llm import parse_chat_model
from src.prompts.fact_check import fact_check_system_prompt, fact_check_user_prompt


class FactCheckAgent(BaseAgent[FactCheckInput, FactCheckOutput]):
    name = "fact-checker"

    async def run(self, params: FactCheckInput) -> FactCheckOutput:
        return await parse_chat_model(
            self.client,
            FactCheckOutput,
            phase=f"fact-check ({params.use_case.id})",
            model=settings.FACT_CHECK_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": fact_check_system_prompt()},
                {
                    "role": "user",
                    "content": fact_check_user_prompt(
                        params.company_profile,
                        params.use_case,
                    ),
                },
            ],
        )
