from datetime import date

import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.client.models import TextChunk, WebSearchTool

from src.core.config import settings
from src.core.schemas import ResearchInput, ResearchResult
from src.prompts.web_search import research_prompt, web_search_system_prompt


class ResearchAgent:
    name = "researcher"

    async def run(self, params: ResearchInput) -> ResearchResult:
        session = workflows_mistralai.RemoteSession()
        agent = workflows_mistralai.Agent(
            model=settings.WEB_SEARCH_MODEL,
            name="research-agent",
            description="Researches companies via web search",
            instructions=web_search_system_prompt(date.today()),
            tools=[WebSearchTool()],
        )

        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=research_prompt(params.company_query),
            session=session,
            max_turns=settings.WEB_SEARCH_MAX_ROUNDS,
        )

        text = "\n".join(
            output.text for output in outputs if isinstance(output, TextChunk)
        )
        if not text.strip():
            raise RuntimeError("research produced no usable text")
        return ResearchResult(text=text)
