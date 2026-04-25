from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import genai_use_cases_system_prompt, genai_use_cases_user_prompt
from src.schemas import (
    GenAIUseCasesInput,
    GenAIUseCasesOutput,
)
from src.utils import parse_chat_model


class GenAIUseCasesAgent(BaseAgent[GenAIUseCasesInput, GenAIUseCasesOutput]):
    name = "genai-use-cases"

    async def run(self, params: GenAIUseCasesInput) -> GenAIUseCasesOutput:
        return await parse_chat_model(
            self.client,
            GenAIUseCasesOutput,
            phase="GenAI use-case generation",
            model=settings.GENAI_USE_CASES_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.GENAI_USE_CASES_LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": genai_use_cases_system_prompt()},
                {
                    "role": "user",
                    "content": genai_use_cases_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.opportunity_map,
                    ),
                },
            ],
        )
