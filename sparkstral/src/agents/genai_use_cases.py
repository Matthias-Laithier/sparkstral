from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.schemas import SingleUseCaseGeneration, SingleUseCaseInput
from src.llm import parse_chat_model
from src.prompts.generation import (
    single_use_case_system_prompt,
    single_use_case_user_prompt,
)


class SingleUseCaseAgent(
    BaseAgent[SingleUseCaseInput, SingleUseCaseGeneration],
):
    name = "single-use-case-generator"

    async def run(self, params: SingleUseCaseInput) -> SingleUseCaseGeneration:
        return await parse_chat_model(
            self.client,
            SingleUseCaseGeneration,
            phase=f"use-case generation (uc_{params.use_case_index})",
            model=settings.GENAI_USE_CASES_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.GENAI_USE_CASES_LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": single_use_case_system_prompt()},
                {
                    "role": "user",
                    "content": single_use_case_user_prompt(params),
                },
            ],
        )
