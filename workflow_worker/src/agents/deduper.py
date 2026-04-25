from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import deduper_system_prompt, deduper_user_prompt
from src.schemas import DeduplicatedUseCasePool, DeduplicateUseCasesInput
from src.utils import parse_chat_model


class UseCaseDeduperAgent(BaseAgent[DeduplicateUseCasesInput, DeduplicatedUseCasePool]):
    name = "use-case-deduper"

    async def run(self, params: DeduplicateUseCasesInput) -> DeduplicatedUseCasePool:
        return await parse_chat_model(
            self.client,
            DeduplicatedUseCasePool,
            phase="use-case deduplication",
            model=settings.USE_CASE_DEDUPER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": deduper_system_prompt()},
                {
                    "role": "user",
                    "content": deduper_user_prompt(params.candidates),
                },
            ],
        )
