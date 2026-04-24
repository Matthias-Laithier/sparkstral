from mistralai.client.models import (
    ConversationResponse,
    MessageOutputEntry,
    TextChunk,
    WebSearchTool,
)

from src.core.config import settings
from src.workflow.agents.base import BaseAgent
from src.workflow.schemas import (
    CompanyProfileInput,
    CompanyProfileOutput,
    CompanyProfilerResult,
)


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
            return CompanyProfilerResult(
                research_text="",
                profile=CompanyProfileOutput(notes=f"Research failed: {exc}"),
            )
        try:
            profile = await self._structure(input.company_query, research_text)
        except Exception as exc:
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
        response = await self.client.beta.conversations.start_async(
            model=settings.COMPANY_PROFILER_SEARCH_MODEL,
            inputs=(
                f"Research this company: {company_query}\n\n"
                "Gather: official or common company name; primary industry; 2-5"
                " business lines; key customers or segments if public; 2-5 strategic"
                " priorities; and do not forget to include the source URL next to each fact.\n"
                "Use few sources: prefer English Wikipedia, plus at most one or two"
                " other reliable pages."
            ),
            tools=[WebSearchTool()],  # type: ignore[arg-type]
        )
        return _extract_text(response)

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


def _extract_text(response: ConversationResponse) -> str:
    parts: list[str] = []
    for entry in response.outputs:
        if not isinstance(entry, MessageOutputEntry):
            continue
        content = entry.content
        if isinstance(content, str):
            parts.append(content)
            continue
        for chunk in content:
            if isinstance(chunk, TextChunk):
                parts.append(chunk.text)
    return "".join(parts)
