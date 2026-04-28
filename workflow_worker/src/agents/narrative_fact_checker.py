from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.schemas import NarrativeFactCheckInput, NarrativeFactCheckOutput
from src.llm import parse_chat_model
from src.prompts.fact_check import (
    fact_check_narratives_system_prompt,
    fact_check_narratives_user_prompt,
)


class NarrativeFactCheckAgent(
    BaseAgent[NarrativeFactCheckInput, NarrativeFactCheckOutput],
):
    name = "narrative-fact-checker"

    async def run(self, params: NarrativeFactCheckInput) -> NarrativeFactCheckOutput:
        return await parse_chat_model(
            self.client,
            NarrativeFactCheckOutput,
            phase="narrative fact-check",
            model=settings.FACT_CHECK_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": fact_check_narratives_system_prompt(),
                },
                {
                    "role": "user",
                    "content": fact_check_narratives_user_prompt(
                        params.company_profile,
                        params.narratives,
                    ),
                },
            ],
        )
