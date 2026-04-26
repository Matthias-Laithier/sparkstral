from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., description="Raw company name entered by the user.")


class CompanyResolutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_query: str


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


class CompanyEvidenceClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str = Field(..., description="Concise factual claim from company research.")
    source_url: str = Field(..., description="Full http(s) URL supporting the claim.")
    citation: str = Field(
        ...,
        description="Short quote, citation, or faithful detail from the source.",
    )

    @field_validator("source_url")
    @classmethod
    def source_url_must_be_full_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("source_url must start with http:// or https://")
        return value


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
    business_lines: list[str] = Field(..., min_length=1)
    key_customers: list[str] = Field(..., min_length=1)
    customer_segments: list[str] = Field(..., min_length=1)
    strategic_priorities: list[str] = Field(..., min_length=1)
    recent_strategic_initiatives: list[str] = Field(..., min_length=1)
    geography_markets: list[str] = Field(..., min_length=1)
    operational_context: list[str] = Field(..., min_length=1)
    regulatory_context: list[str] = Field(..., min_length=1)
    customer_market_pressure: list[str] = Field(..., min_length=1)
    growth_opportunities: list[str] = Field(..., min_length=1)
    technology_transformation_context: list[str] = Field(..., min_length=1)
    claims: list[CompanyEvidenceClaim] = Field(..., min_length=15)


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


class PainPointStructuringInput(BaseModel):
    company_profile: CompanyProfileOutput


class GenAIMechanism(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mechanisms: list[
        Literal[
            "retrieval_augmented_generation",
            "document_understanding",
            "structured_generation",
            "multi_step_reasoning",
            "tool_orchestration",
            "conversational_interface",
            "summarization",
            "scenario_generation",
            "decision_support",
            "multimodal_understanding",
        ]
    ] = Field(..., min_length=1)
    why_genai_is_needed: str
    why_classical_software_is_not_enough: str
    why_classical_ml_or_optimization_is_not_enough: str


class SourceBackedMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., description="Name of the metric or benchmark.")
    value: str = Field(
        ...,
        description=(
            "Exact metric value, copied or faithfully summarized from a source."
        ),
    )
    source_url: str = Field(..., description="Full URL supporting the metric.")
    source_quote_or_evidence: str = Field(
        ...,
        description="Short explanation of what the source says.",
    )
    applies_to: Literal[
        "company",
        "industry",
        "similar_case",
        "regulation",
        "market",
        "technology_benchmark",
    ]
    confidence: Literal["low", "medium", "high"]


class PilotKPI(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kpi: str
    why_it_matters: str
    measurement_method: str
    target_direction: Literal["increase", "decrease", "maintain"]
    baseline_needed: str


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
    genai_mechanism: GenAIMechanism
    required_data: str = Field(
        ...,
        description="Data and systems needed to build and run it.",
    )
    qualitative_impact: str = Field(
        ...,
        description=(
            "Qualitative business or operational impact, without invented numbers."
        ),
    )
    source_backed_metrics: list[SourceBackedMetric] = Field(
        ...,
        description=(
            "Metrics or benchmarks directly supported by evidence_sources; empty when "
            "no sourced metric exists."
        ),
    )
    pilot_kpis: list[PilotKPI] = Field(
        ...,
        min_length=2,
        description="KPIs to validate in a pilot, without invented numeric targets.",
    )
    why_iconic: str
    feasibility_notes: str
    risks: list[str] = Field(
        ...,
        min_length=1,
        description="Main risks (technical, compliance, org, model).",
    )
    linked_pain_points: list[str] = Field(
        ...,
        min_length=1,
        description="Pain point titles from PainPointProfilerOutput.",
    )
    evidence_sources: list[str] = Field(..., min_length=1)
    ideation_lens: str

    @model_validator(mode="after")
    def source_backed_metrics_use_candidate_evidence(self) -> Self:
        evidence_sources = set(self.evidence_sources)
        for metric in self.source_backed_metrics:
            if metric.source_url not in evidence_sources:
                raise ValueError(
                    "source_backed_metrics.source_url must be present in "
                    "evidence_sources"
                )
        return self


class GenAIUseCaseCandidatePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_cases: list[GenAIUseCaseCandidate] = Field(
        ...,
        min_length=5,
        max_length=12,
        description="Candidate pool of 5-12 GenAI use cases.",
    )


GenAIUseCasePersona = Literal[
    "grounded consultant",
    "moonshot strategist",
    "why not? inventor",
]
GenAIUseCaseIdPrefix = Literal["grounded_uc", "moonshot_uc", "why_not_uc"]


class GenAIUseCaseCandidateBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_cases: list[GenAIUseCaseCandidate] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 GenAI use cases from one generator persona.",
    )


class UseCaseDeduplicationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retained_use_case_ids: list[str] = Field(
        ...,
        min_length=5,
        description=(
            "Existing use case IDs to keep after removing very similar duplicates."
        ),
    )


class UseCaseScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    strengths: list[str] = Field(..., min_length=1)
    weaknesses: list[str] = Field(..., min_length=1)
    rationale: str
    company_relevance: int = Field(..., ge=1, le=5)
    business_impact: int = Field(..., ge=1, le=5)
    iconicness: int = Field(..., ge=1, le=5)
    genai_fit: int = Field(..., ge=1, le=5)
    feasibility: int = Field(..., ge=1, le=5)
    evidence_strength: int = Field(..., ge=1, le=5)
    penalties: list[str]
    weighted_total: float = Field(..., ge=1, le=5)


class UseCaseGrade(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    strengths: list[str] = Field(..., min_length=1)
    weaknesses: list[str] = Field(..., min_length=1)
    rationale: str
    company_relevance: int = Field(..., ge=1, le=5)
    business_impact: int = Field(..., ge=1, le=5)
    iconicness: int = Field(..., ge=1, le=5)
    genai_fit: int = Field(..., ge=1, le=5)
    feasibility: int = Field(..., ge=1, le=5)
    evidence_strength: int = Field(..., ge=1, le=5)
    penalties: list[str]


class UseCaseGradePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grades: list[UseCaseGrade] = Field(..., min_length=1)


class GradedUseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: GenAIUseCaseCandidate
    score: UseCaseScore


class GradedUseCasePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graded_use_cases: list[GradedUseCase] = Field(..., min_length=1)


class FinalSelectionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected: list[GradedUseCase] = Field(..., min_length=3, max_length=3)


class GradeUseCasesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput
    use_cases: list[GenAIUseCaseCandidate] = Field(..., min_length=1)


class DeduplicateUseCasesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput
    use_cases: list[GenAIUseCaseCandidate] = Field(..., min_length=1)


class GenAIUseCaseCandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput


class GenAIUseCasePersonaInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput
    ideation_lens: GenAIUseCasePersona
    id_prefix: GenAIUseCaseIdPrefix


class PipelineOutput(BaseModel):
    id: int
    kind: Literal["text", "json"]
    text: str | None = None
    data: dict[str, Any] | None = None


class MarkdownReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    pain_points: PainPointProfilerOutput
    final_selection: FinalSelectionOutput


class MarkdownReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str


class SparkstralWorkflowResult(BaseModel):
    outputs: list[PipelineOutput]
    final: str
