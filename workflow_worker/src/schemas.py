from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., description="Raw company name entered by the user.")


class CompanyProfileInput(BaseModel):
    company_query: str = Field(..., description="Raw company name entered by the user.")


class ResearchResult(BaseModel):
    text: str


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
        description="Optional caveats about the extracted profile.",
    )


class CompanyProfileStructuringInput(BaseModel):
    company_query: str
    research_text: str


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


class PainPointResearchInput(BaseModel):
    company_profile: CompanyProfileOutput


class PainPointStructuringInput(BaseModel):
    company_profile: CompanyProfileOutput
    research_text: str


class GenAIUseCaseItem(BaseModel):
    title: str
    target_users: list[str] = Field(
        ...,
        min_length=1,
        description="Clients, teams, or user groups the use case serves.",
    )
    business_problem: str = Field(..., description="Problem the use case addresses.")
    why_this_company: str = Field(
        ...,
        description="Why this use case fits this company and context.",
    )
    genai_solution: str = Field(
        ...,
        description="What the GenAI solution does (concretely, not a product pitch).",
    )
    required_data: str = Field(
        ...,
        description="Data and systems needed to build and run it.",
    )
    expected_impact: str = Field(
        ...,
        description="Expected business or operational impact.",
    )
    risks: list[str] = Field(
        ...,
        min_length=1,
        description="Main risks (technical, compliance, org, model).",
    )


class GenAIUseCasesOutput(BaseModel):
    use_cases: list[GenAIUseCaseItem] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 high-impact GenAI use cases.",
    )


class GenAIUseCasesInput(BaseModel):
    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput


class PipelineOutput(BaseModel):
    id: int
    kind: Literal["text", "json"]
    text: str | None = None
    data: dict[str, Any] | None = None


class SparkstralWorkflowResult(BaseModel):
    outputs: list[PipelineOutput]
    final: GenAIUseCasesOutput
