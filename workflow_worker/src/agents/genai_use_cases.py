from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import genai_use_cases_system_prompt, genai_use_cases_user_prompt
from src.schemas import (
    GenAIUseCaseCandidateBatch,
    GenAIUseCasePersonaInput,
)
from src.utils import parse_chat_model


class GenAIUseCasesAgent(
    BaseAgent[GenAIUseCasePersonaInput, GenAIUseCaseCandidateBatch]
):
    name = "genai-use-cases"

    async def run(
        self,
        params: GenAIUseCasePersonaInput,
    ) -> GenAIUseCaseCandidateBatch:
        return await parse_chat_model(
            self.client,
            GenAIUseCaseCandidateBatch,
            phase=f"GenAI use-case generation ({params.ideation_lens})",
            model=settings.GENAI_USE_CASES_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.GENAI_USE_CASES_LLM_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": genai_use_cases_system_prompt(
                        params.ideation_lens,
                        params.id_prefix,
                    ),
                },
                {
                    "role": "user",
                    "content": genai_use_cases_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.ideation_lens,
                        params.id_prefix,
                    ),
                },
            ],
        )
