import mistralai.workflows as workflows
from mistralai.client import Mistral
from mistralai.client.models import (
    ConversationResponse,
    MessageOutputEntry,
    TextChunk,
    WebSearchTool,
)

from src.core.config import settings


@workflows.activity()
async def search_company_description(company_name: str) -> str:
    client = Mistral(api_key=settings.mistral_api_key)
    response = await client.beta.conversations.start_async(
        model="mistral-small-latest",
        inputs=(
            f"What does the company '{company_name}' do?"
            " Give me a concise 2-3 sentence description."
        ),
        # Mypy: `list` is invariant; the SDK types `tools` as list[ToolUnion] but
        # `[WebSearchTool()]` is inferred as list[WebSearchTool].
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
