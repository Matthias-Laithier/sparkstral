import asyncio

import mistralai.workflows as workflows
from mistralai.client import Mistral
from mistralai.client.models import (
    ConversationResponse,
    MessageOutputEntry,
    TextChunk,
    WebSearchTool,
)
from pydantic import BaseModel

from src.core.config import settings


class CompanyInput(BaseModel):
    company_name: str


@workflows.activity()
async def search_company_description(company_name: str) -> str:
    client = Mistral(api_key=settings.mistral_api_key)
    response = await client.beta.conversations.start_async(
        model="mistral-medium-latest",
        inputs=(
            f"What does the company '{company_name}' do?"
            " Give me a concise 2-3 sentence description."
        ),
        tools=[WebSearchTool()],  # type: ignore[arg-type]
    )
    return _extract_text(response)


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


@workflows.workflow.define(
    name="company-description",
    workflow_display_name="Company Description",
    workflow_description="Web search: short description of what a company does",
    enforce_determinism=False,
)
class CompanyDescriptionWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: CompanyInput) -> str:
        return await search_company_description(input.company_name)


async def main() -> None:
    await workflows.run_worker([CompanyDescriptionWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
