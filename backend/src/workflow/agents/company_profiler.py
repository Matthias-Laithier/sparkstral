import logging

from src.core.config import settings
from src.workflow.agents.base import BaseAgent
from src.workflow.agents.web_search import WebSearchAgent, WebSearchInput
from src.workflow.schemas import (
    CompanyProfileInput,
    CompanyProfileOutput,
    CompanyProfilerResult,
)

logger = logging.getLogger(__name__)


class CompanyProfilerAgent(BaseAgent):
    name = "company-profiler"
    system_prompt = (
        "You are a data extraction assistant. Given research notes about a company,"
        " extract and return a structured profile.\n"
        "Only include information supported by the research.\n"
        "For every evidence item, `source` must be a full URL (https preferred),"
        " from the research — not a site name only."
    )

    async def run(self, input: CompanyProfileInput) -> CompanyProfilerResult:  # type: ignore[override]
        try:
            research_text = await self._research(input.company_query)
        except Exception as exc:
            logger.exception("Company research phase failed")
            return CompanyProfilerResult(
                research_text="",
                profile=CompanyProfileOutput(notes=f"Research failed: {exc}"),
            )
        try:
            profile = await self._structure(input.company_query, research_text)
        except Exception as exc:
            logger.exception("Company structuring phase failed")
            return CompanyProfilerResult(
                research_text=research_text,
                profile=CompanyProfileOutput(
                    notes=f"Structuring failed: {exc}",
                ),
            )
        return CompanyProfilerResult(
            research_text=research_text,
            profile=profile,
        )

    async def _research(self, company_query: str) -> str:
        agent = WebSearchAgent(client=self.client)
        result = await agent.run(
            WebSearchInput(
                prompt=(
                    f"Research this company: {company_query}\n\n"
                    "Gather: official or common company name; primary industry; 2-5"
                    " business lines; key customers or segments if public;"
                    " 2-5 strategic"
                    " priorities; include the source URL next to each fact.\n"
                    "Use few sources: prefer Wikipedia, plus at most one or two other"
                    " reliable pages."
                )
            )
        )
        return result.text

    async def _structure(
        self, company_query: str, research_text: str
    ) -> CompanyProfileOutput:
        parsed = await self.client.chat.parse_async(
            CompanyProfileOutput,
            model=settings.COMPANY_PROFILER_AGENT_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Company query: {company_query}\n\n"
                        f"Research notes:\n{research_text}\n\n"
                        "Return the structured profile with only the most relevant"
                        " information. "
                        "Be concise: 2-5 items each for business_lines, key_customers,"
                        " and strategic_priorities."
                    ),
                },
            ],
        )
        if (
            parsed.choices
            and parsed.choices[0].message
            and parsed.choices[0].message.parsed is not None
        ):
            return parsed.choices[0].message.parsed
        raise ValueError("Structuring phase returned no parsed output")
