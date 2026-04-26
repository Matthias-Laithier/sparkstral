from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import genai_use_cases_system_prompt, genai_use_cases_user_prompt
from src.schemas import GenAIUseCaseCandidateInput, GenAIUseCaseGeneration
from src.utils import parse_chat_model


class GenAIUseCasesAgent(
    BaseAgent[GenAIUseCaseCandidateInput, GenAIUseCaseGeneration],
):
    name = "genai-use-cases"

    async def run(
        self,
        params: GenAIUseCaseCandidateInput,
    ) -> GenAIUseCaseGeneration:
        return await parse_chat_model(
            self.client,
            GenAIUseCaseGeneration,
            phase="GenAI use-case generation",
            model=settings.GENAI_USE_CASES_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.GENAI_USE_CASES_LLM_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": genai_use_cases_system_prompt(),
                },
                {
                    "role": "user",
                    "content": genai_use_cases_user_prompt(params.company_profile),
                },
            ],
        )
