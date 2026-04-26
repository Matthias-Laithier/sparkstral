import mistralai.workflows.plugins.mistralai as workflows_mistralai
import pytest

from src import worker
from src.schemas import CompanyInput, PipelineOutput, SparkstralWorkflowResult


@pytest.mark.asyncio
async def test_sparkstral_workflow_returns_le_chat_output(monkeypatch) -> None:
    assistant_messages = []

    async def run_sparkstral_pipeline(
        params: CompanyInput,
        status_callback=None,
    ) -> SparkstralWorkflowResult:
        assert params.company_name == "Acme"
        assert status_callback is not None
        await status_callback("Researching company context...")
        await status_callback("Generating candidate use cases...")
        await status_callback("Scoring opportunities...")
        return SparkstralWorkflowResult(
            outputs=[
                PipelineOutput(
                    id=1,
                    kind="text",
                    text="Research trace",
                )
            ],
            final="# GenAI Opportunity Report\n\nFinal markdown.",
        )

    async def send_assistant_message(text, *, canvas=None) -> None:
        assistant_messages.append((text, canvas))

    monkeypatch.setattr(
        workflows_mistralai,
        "send_assistant_message",
        send_assistant_message,
    )
    monkeypatch.setattr(worker.workflow, "uuid4", lambda: "test-canvas-id")
    monkeypatch.setattr(worker, "run_sparkstral_pipeline", run_sparkstral_pipeline)

    response_payload = await worker.SparkstralWorkflow().run(
        CompanyInput(company_name="Acme")
    )
    response = workflows_mistralai.ChatAssistantWorkflowOutput.model_validate(
        response_payload
    )
    response_json = response.model_dump(mode="json", by_alias=True)

    assert isinstance(response, workflows_mistralai.ChatAssistantWorkflowOutput)
    assert response_json["content"][0]["text"] == (
        "Sparkstral analysis complete. The final report is attached."
    )
    assert response_json["content"][1]["resource"]["canvas"] == {
        "type": "text/markdown",
        "title": "Sparkstral report for Acme",
        "content": "# GenAI Opportunity Report\n\nFinal markdown.",
        "language": None,
    }
    assert response_json["structuredContent"] == {
        "outputs": [
            {
                "id": 1,
                "kind": "text",
                "text": "Research trace",
                "data": None,
            }
        ],
        "final": "# GenAI Opportunity Report\n\nFinal markdown.",
    }
    assert assistant_messages[:3] == [
        ("Researching company context...", None),
        ("Generating candidate use cases...", None),
        ("Scoring opportunities...", None),
    ]
    assert assistant_messages[3][0][0].text == (
        "Sparkstral analysis complete. The final report is attached."
    )
    assert assistant_messages[3][0][1].resource.canvas.content == (
        "# GenAI Opportunity Report\n\nFinal markdown."
    )
    assert assistant_messages[3][1] is None
