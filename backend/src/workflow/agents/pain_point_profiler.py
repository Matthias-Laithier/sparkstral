import json

from mistralai.client.models import (
    ConversationResponse,
    MessageOutputEntry,
    TextChunk,
    WebSearchTool,
)

from src.core.config import settings
from src.workflow.agents.base import BaseAgent
from src.workflow.schemas import (
    CompanyProfileOutput,
    PainPointProfilerInput,
    PainPointProfilerOutput,
    PainPointProfilerResult,
)


class PainPointProfilerAgent(BaseAgent):
    name = "pain-point-profiler"
    system_prompt = (
        "You are an analyst. Given research notes, extract major pain points,"
        " industry gaps, or unmet needs relevant to the company and its field.\n"
        "Only include points supported by the research. Assign prominence 1-10 from"
        " the evidence strength and business impact. Each pain point's sources"
        " must be full URL strings from the research."
    )

    async def run(  # type: ignore[override]
        self, input: PainPointProfilerInput
    ) -> PainPointProfilerResult:
        ctx = _company_context(input.company_profile)
        try:
            research_text = await self._research(ctx)
        except Exception:
            return PainPointProfilerResult(
                research_text="",
                output=PainPointProfilerOutput(pain_points=[]),
            )
        try:
            out = await self._structure(ctx, research_text)
            return PainPointProfilerResult(
                research_text=research_text,
                output=out,
            )
        except Exception:
            return PainPointProfilerResult(
                research_text=research_text,
                output=PainPointProfilerOutput(pain_points=[]),
            )

    async def _research(self, company_context: str) -> str:
        response = await self.client.beta.conversations.start_async(
            model=settings.PAIN_POINT_PROFILER_SEARCH_MODEL,
            inputs=(
                "Search the web for major pain points, unmet needs, and structural"
                f" challenges in the company's field.\n\n{company_context}\n\n"
                "Web search scope: do not use many different websites. Prefer a"
                " relevant Wikipedia article (industry, technology, or market) when it"
                " exists, and add at most one or two other reputable sources. Keep"
                " searches minimal.\n"
                "Include the full URL of the source for each relevant finding you cite."
            ),
            tools=[WebSearchTool()],  # type: ignore[arg-type]
        )
        return _extract_text(response)

    async def _structure(
        self, company_context: str, research_text: str
    ) -> PainPointProfilerOutput:
        parsed = await self.client.chat.parse_async(
            PainPointProfilerOutput,
            model=settings.PAIN_POINT_PROFILER_AGENT_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{company_context}\n\n"
                        f"Research notes:\n{research_text}\n\n"
                        "Return 3-8 pain points. Be specific and avoid duplication."
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


def _company_context(profile: CompanyProfileOutput) -> str:
    return (
        "Known company profile (from prior step):\n"
        + json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False)
    )


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
