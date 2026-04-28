from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.schemas import MarkdownReport, MarkdownReportInput, ReportNarratives
from src.llm import parse_chat_model
from src.prompts.reporter import (
    build_report_markdown,
    narrative_system_prompt,
    narrative_user_prompt,
)


class MarkdownReporterAgent(BaseAgent[MarkdownReportInput, MarkdownReport]):
    name = "markdown-reporter"

    async def run(self, params: MarkdownReportInput) -> MarkdownReport:
        narratives = await parse_chat_model(
            self.client,
            ReportNarratives,
            phase="report narratives",
            model=settings.MARKDOWN_REPORTER_AGENT_MODEL,
            max_tokens=4096,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": narrative_system_prompt()},
                {
                    "role": "user",
                    "content": narrative_user_prompt(
                        params.company_profile,
                        params.final_selection,
                    ),
                },
            ],
        )

        markdown = build_report_markdown(
            params.company_profile,
            params.final_selection,
            narratives,
        )
        return MarkdownReport(markdown=markdown)
