import asyncio
from datetime import timedelta
from typing import Any

import mistralai.workflows as workflows
from mistralai.workflows import workflow
from pydantic import BaseModel, ConfigDict

# Activity and schema modules pull in mistralai.client / httpx. The Temporal
# workflow sandbox blocks those imports unless they run under pass-through.
with workflow.unsafe.imports_passed_through():
    from src.workflow.activities import profile_company, profile_pain_points
    from src.workflow.schemas import (
        CompanyProfileInput,
        PainPointProfilerInput,
        SparkstralStep,
        SparkstralWorkflowResult,
    )
    from src.workflow.utils import append_sparkstral_step


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
        company = await profile_company(
            CompanyProfileInput(company_query=params.company_name)
        )
        steps: list[SparkstralStep] = []
        append_sparkstral_step(
            steps,
            label="Company research (web search)",
            phase="research",
            content=company.research_text,
        )
        append_sparkstral_step(
            steps,
            label="Company profile (structured)",
            phase="structure",
            data=company.profile.model_dump(mode="json"),
        )
        pain = await profile_pain_points(
            PainPointProfilerInput(company_profile=company.profile)
        )
        append_sparkstral_step(
            steps,
            label="Pain point research (web search)",
            phase="research",
            content=pain.research_text,
        )
        append_sparkstral_step(
            steps,
            label="Pain points (structured)",
            phase="structure",
            data=pain.output.model_dump(mode="json"),
        )
        return SparkstralWorkflowResult(steps=steps).model_dump(mode="json")


async def main() -> None:
    await workflows.run_worker([SparkstralWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
