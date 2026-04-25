from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., description="Raw company name entered by the user.")


class CompanyResolutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_query: str


class CompanyProfileInput(BaseModel):
    company_query: str = Field(..., description="Raw company name entered by the user.")


class ResearchResult(BaseModel):
    text: str


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str = Field(
        ..., description="Short factual claim used to build the profile."
    )
    source: str = Field(
        ...,
        description="URL string (https recommended) supporting the claim.",
    )


class CompanyResolutionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_name: str
    resolved_name: str
    website: str
    headquarters_country: str
    primary_industry: str
    ambiguity_notes: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(..., min_length=1)


class CompanyResolutionStructuringInput(BaseModel):
    company_query: str
    research_text: str


class CompanyProfileOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    industry: str
    business_lines: list[str]
    key_customers: list[str]
    strategic_priorities: list[str]
    evidence: list[EvidenceItem] = Field(..., min_length=1)
    notes: str = Field(
        ...,
        description="Optional caveats about the extracted profile.",
    )


class CompanyProfileStructuringInput(BaseModel):
    company_query: str
    research_text: str


class PainPointItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Short name for the pain point or gap.")
    description: str = Field(..., description="What is going on and why it matters.")
    prominence: int = Field(
        ..., ge=1, le=10, description="Importance 1 (low) to 10 (high) from research."
    )
    sources: list[str] = Field(
        ...,
        min_length=1,
        description="URL strings for facts behind this point.",
    )


class PainPointProfilerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pain_points: list[PainPointItem] = Field(..., min_length=3, max_length=8)


class PainPointResearchInput(BaseModel):
    company_profile: CompanyProfileOutput


class PainPointStructuringInput(BaseModel):
    company_profile: CompanyProfileOutput
    research_text: str


class OpportunityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    business_line: str
    linked_pain_points: list[str] = Field(..., min_length=1)
    why_it_matters: str
    why_genai_is_suitable: str
    likely_data_sources: list[str] = Field(..., min_length=1)
    evidence_sources: list[str] = Field(..., min_length=1)


class OpportunityMapOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunities: list[OpportunityItem] = Field(..., min_length=3, max_length=8)
    summary: str


class OpportunityMapInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput


class GenAIUseCaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
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
    why_iconic: str
    feasibility_notes: str
    risks: list[str] = Field(
        ...,
        min_length=1,
        description="Main risks (technical, compliance, org, model).",
    )
    linked_opportunities: list[str] = Field(..., min_length=1)
    evidence_sources: list[str] = Field(..., min_length=1)
    ideation_lens: str


class GenAIUseCaseCandidatePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_cases: list[GenAIUseCaseCandidate] = Field(
        ...,
        min_length=8,
        max_length=12,
        description="Candidate pool of 8-12 GenAI use cases.",
    )


class DeduplicateUseCasesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: GenAIUseCaseCandidatePool


class DeduplicatedUseCasePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_cases: list[GenAIUseCaseCandidate] = Field(..., min_length=6, max_length=10)
    removed_or_merged: list[str]
    rationale: str


class UseCaseScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    company_relevance: int = Field(..., ge=1, le=5)
    business_impact: int = Field(..., ge=1, le=5)
    iconicness: int = Field(..., ge=1, le=5)
    genai_fit: int = Field(..., ge=1, le=5)
    feasibility: int = Field(..., ge=1, le=5)
    evidence_strength: int = Field(..., ge=1, le=5)
    total: int = Field(..., ge=6, le=30)
    rationale: str
    strengths: list[str] = Field(..., min_length=1)
    weaknesses: list[str] = Field(..., min_length=1)


class GradedUseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: GenAIUseCaseCandidate
    score: UseCaseScore


class GradedUseCasePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graded_use_cases: list[GradedUseCase] = Field(..., min_length=6)


class GradeUseCasesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput
    opportunity_map: OpportunityMapOutput
    use_cases: list[GenAIUseCaseCandidate] = Field(..., min_length=1)


class GenAIUseCaseCandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput
    opportunity_map: OpportunityMapOutput


class PipelineOutput(BaseModel):
    id: int
    kind: Literal["text", "json"]
    text: str | None = None
    data: dict[str, Any] | None = None


class SparkstralWorkflowResult(BaseModel):
    outputs: list[PipelineOutput]
    final: GradedUseCasePool
