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
    CompanyResolutionStatus,
)


class CompanyProfilerAgent(BaseAgent):
    name = "company-profiler"
    system_prompt = (
        "You are a data extraction assistant. Given research notes about a company,"
        " extract and return a structured profile.\n"
        "Only include information supported by the research.\n"
        "Status rules:\n"
        '  "found"     — company clearly identified\n'
        '  "not_found" — company cannot be confirmed\n'
        '  "ambiguous" — multiple companies match equally; prefer the dominant one\n'
        "Set confidence based on how complete and consistent the research is.\n"
        "For every evidence item, `source` must be a full URL (https preferred),"
        " from the research — not a site name only."
    )

    async def run(self, input: CompanyProfileInput) -> CompanyProfileOutput:  # type: ignore[override]
        try:
            research_text = await self._research(input.company_query)
            return await self._structure(input.company_query, research_text)
        except Exception as exc:
            return CompanyProfileOutput(
                status=CompanyResolutionStatus.NOT_FOUND,
                confidence=0.0,
                notes=f"Profiling failed: {exc}",
            )

    async def _research(self, company_query: str) -> str:
        response = await self.client.beta.conversations.start_async(
            model=settings.COMPANY_PROFILER_SEARCH_MODEL,
            inputs=(
                f"Research this company thoroughly: {company_query}\n"
                "Include the full URL of the source for each factual point you cite."
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
