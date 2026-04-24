from typing import Any, Literal

from pydantic import BaseModel, Field


class CompanyProfileInput(BaseModel):
    company_query: str = Field(..., description="Raw company name entered by the user.")


class EvidenceItem(BaseModel):
    claim: str = Field(
        ..., description="Short factual claim used to build the profile."
    )
    source: str = Field(
        ...,
        description="URL string (https recommended) supporting the claim.",
    )


class CompanyProfileOutput(BaseModel):
    company_name: str = ""
    industry: str = ""
    business_lines: list[str] = Field(default_factory=list)
    key_customers: list[str] = Field(default_factory=list)
    strategic_priorities: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    notes: str = Field(
        default="",
        description="Optional caveats or extraction errors.",
    )


class CompanyProfilerResult(BaseModel):
    research_text: str
    profile: CompanyProfileOutput


class PainPointItem(BaseModel):
    title: str = Field(..., description="Short name for the pain point or gap.")
    description: str = Field(..., description="What is going on and why it matters.")
    prominence: int = Field(
        ..., ge=1, le=10, description="Importance 1 (low) to 10 (high) from research."
    )
    sources: list[str] = Field(
        default_factory=list,
        description="URL strings for facts behind this point.",
    )


class PainPointProfilerOutput(BaseModel):
    pain_points: list[PainPointItem] = Field(default_factory=list)


class PainPointProfilerInput(BaseModel):
    company_profile: CompanyProfileOutput


class PainPointProfilerResult(BaseModel):
    research_text: str
    output: PainPointProfilerOutput


class SparkstralStep(BaseModel):
    id: int
    label: str
    phase: Literal["research", "structure"]
    content: str | None = None
    data: dict[str, Any] | None = None


class SparkstralWorkflowResult(BaseModel):
    steps: list[SparkstralStep]
