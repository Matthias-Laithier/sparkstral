import asyncio
from datetime import timedelta

import mistralai.workflows as workflows
from mistralai.workflows import workflow
from pydantic import BaseModel, ConfigDict

# Activity module pulls in mistralai.client / httpx. The Temporal workflow sandbox
# blocks that import unless it runs under pass-through (see core/sandbox.py).
with workflow.unsafe.imports_passed_through():
    from src.activities.company_description import search_company_description


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str


@workflows.workflow.define(
    name="company-description",
    workflow_display_name="Company Description",
    workflow_description="Web search: short description of what a company does",
    execution_timeout=timedelta(minutes=10),
)
class CompanyDescriptionWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: CompanyInput) -> str:
        return await search_company_description(params.company_name)


async def main() -> None:
    await workflows.run_worker([CompanyDescriptionWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
