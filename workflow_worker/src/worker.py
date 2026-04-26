import asyncio
from datetime import timedelta

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.workflows import workflow

# Activity and schema modules pull in mistralai.client / httpx. `src.config` loads
# pydantic-settings/dotenv (pathlib), which the workflow sandbox rejects unless the
# import is marked pass-through.
with workflow.unsafe.imports_passed_through():
    from src.config import settings
    from src.pipeline import run_sparkstral_pipeline
    from src.schemas import CompanyInput


@workflows.workflow.define(
    name=settings.DEPLOYMENT_NAME,
    workflow_display_name=settings.DEPLOYMENT_NAME.capitalize(),
    workflow_description="Research a company and return a client-ready GenAI report",
    execution_timeout=timedelta(minutes=10),
)
class SparkstralWorkflow(workflows.InteractiveWorkflow):
    @workflows.workflow.entrypoint
    async def run(
        self,
        params: CompanyInput,
    ) -> workflows_mistralai.ChatAssistantWorkflowOutput:
        result = await run_sparkstral_pipeline(
            params,
            status_callback=workflows_mistralai.send_assistant_message,
        )

        report_canvas = workflows_mistralai.CanvasResource(
            uri=f"sparkstral-report-{workflow.uuid4()}",
            canvas=workflows_mistralai.CanvasPayload(
                type="text/markdown",
                title=f"Sparkstral report for {params.company_name}",
                content=result.final,
            ),
        )
        completion_content: list[
            workflows_mistralai.TextOutput | workflows_mistralai.ResourceOutput
        ] = [
            workflows_mistralai.TextOutput(
                text="Sparkstral analysis complete. The final report is attached."
            ),
            workflows_mistralai.ResourceOutput(resource=report_canvas),
        ]
        await workflows_mistralai.send_assistant_message(
            completion_content,
        )

        return workflows_mistralai.ChatAssistantWorkflowOutput(
            content=completion_content,
            structuredContent=result.model_dump(mode="json"),
        )


async def main() -> None:
    await workflows.run_worker([SparkstralWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
