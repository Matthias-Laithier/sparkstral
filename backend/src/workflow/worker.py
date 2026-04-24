import asyncio
from datetime import timedelta
from typing import Any

import mistralai.workflows as workflows
from mistralai.workflows import workflow
from pydantic import BaseModel, ConfigDict

# Activity and schema modules pull in mistralai.client / httpx. The Temporal
# workflow sandbox blocks those imports unless they run under pass-through.
with workflow.unsafe.imports_passed_through():
    from src.workflow.activities import profile_company
    from src.workflow.schemas import CompanyProfileInput, CompanyResolutionStatus


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str


@workflows.workflow.define(
    name="sparkstral",
    workflow_display_name="Sparkstral",
    workflow_description="Research a company and return a structured profile",
    execution_timeout=timedelta(minutes=10),
)
class SparkstralWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: CompanyInput) -> dict[str, Any]:
        profile = await profile_company(
            CompanyProfileInput(company_query=params.company_name)
        )

        if profile.status != CompanyResolutionStatus.FOUND:
            return profile.model_dump(mode="json")

        # Future: generate use cases here.
        return profile.model_dump(mode="json")


async def main() -> None:
    await workflows.run_worker([SparkstralWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
