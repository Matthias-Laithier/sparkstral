import asyncio
from datetime import timedelta
from typing import Any

import mistralai.workflows as workflows
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
    workflow_description="Research a company and return a structured profile",
    execution_timeout=timedelta(minutes=10),
)
class SparkstralWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: CompanyInput) -> dict[str, Any]:
        result = await run_sparkstral_pipeline(params)
        return result.model_dump(mode="json")


async def main() -> None:
    await workflows.run_worker([SparkstralWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
