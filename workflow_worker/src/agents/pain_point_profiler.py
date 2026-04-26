from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import pain_point_system_prompt, pain_point_user_prompt
from src.schemas import (
    PainPointProfilerOutput,
    PainPointStructuringInput,
)
from src.utils import parse_chat_model


class PainPointProfilerAgent(
    BaseAgent[PainPointStructuringInput, PainPointProfilerOutput]
):
    name = "pain-point-profiler"

    async def run(self, params: PainPointStructuringInput) -> PainPointProfilerOutput:
        return await parse_chat_model(
            self.client,
            PainPointProfilerOutput,
            phase="pain point structuring",
            model=settings.PAIN_POINT_PROFILER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": pain_point_system_prompt()},
                {
                    "role": "user",
                    "content": pain_point_user_prompt(
                        params.company_profile,
                    ),
                },
            ],
        )
