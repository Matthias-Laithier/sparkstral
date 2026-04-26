from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import markdown_reporter_system_prompt, markdown_reporter_user_prompt
from src.schemas import MarkdownReport, MarkdownReportInput
from src.utils import parse_chat_model


class MarkdownReporterAgent(BaseAgent[MarkdownReportInput, MarkdownReport]):
    name = "markdown-reporter"

    async def run(self, params: MarkdownReportInput) -> MarkdownReport:
        return await parse_chat_model(
            self.client,
            MarkdownReport,
            phase="markdown report writing",
            model=settings.MARKDOWN_REPORTER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": markdown_reporter_system_prompt()},
                {
                    "role": "user",
                    "content": markdown_reporter_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.final_selection,
                    ),
                },
            ],
        )
