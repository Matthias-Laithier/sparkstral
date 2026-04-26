from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import final_reporter_system_prompt, final_reporter_user_prompt
from src.schemas import FinalReport, FinalReportInput
from src.utils import parse_chat_model


class FinalReporterAgent(BaseAgent[FinalReportInput, FinalReport]):
    name = "final-reporter"

    async def run(self, params: FinalReportInput) -> FinalReport:
        result = await parse_chat_model(
            self.client,
            FinalReport,
            phase="final report writing",
            model=settings.FINAL_REPORTER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": final_reporter_system_prompt()},
                {
                    "role": "user",
                    "content": final_reporter_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.final_selection,
                    ),
                },
            ],
        )
        ranks = [use_case.rank for use_case in result.top_3_use_cases]
        if ranks != [1, 2, 3]:
            raise RuntimeError("final report use cases must be ranked 1, 2, and 3")
        return result
