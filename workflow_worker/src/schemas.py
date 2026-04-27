from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    company_resolution: CompanyResolutionOutput
    research_text: str


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
    genai_advantage_over_classical_software: str = Field(
        ...,
        description=(
            "Where GenAI adds value beyond rule-based systems and classical NLP; "
            "acknowledge what classical systems still do well."
        ),
    )
    genai_advantage_over_classical_ml: str = Field(
        ...,
        description=(
            "Where GenAI adds value beyond classical ML or optimization; "
            "acknowledge what classical ML handles well."
        ),
    )


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
    company_signal_labels: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Short labels for concrete facts, initiatives, or pressures from the "
            "company profile or research text that motivate this use case."
        ),
    )
    evidence_sources: list[str] = Field(..., min_length=1)

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
        max_length=5,
        description="Batch of 5 GenAI use cases for grading.",
    )


class GenAIUseCaseGeneration(BaseModel):
    """Structured parse output from the GenAI use-case generator."""

    model_config = ConfigDict(extra="forbid")

    ideation_brief: str = Field(
        ...,
        min_length=1,
        description=(
            "Internal batch plan: coverage across GenAI pillars and anti-generic "
            "guardrails, before the use case list. Not for client reports."
        ),
    )
    use_cases: list[GenAIUseCaseCandidate] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="5 distinct, company-specific GenAI use cases.",
    )


class DimensionRubricLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rationale: str = Field(
        ...,
        min_length=1,
        description=(
            "One short sentence explaining the following score. Listed before score "
            "so generation commits to reasoning first."
        ),
    )
    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="1–10 for this rubric line.",
    )


class UseCaseScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    strengths: list[str] = Field(..., min_length=1)
    weaknesses: list[str] = Field(..., min_length=1)
    rationale: str
    company_relevance: DimensionRubricLine
    business_impact: DimensionRubricLine
    iconicness: DimensionRubricLine
    genai_fit: DimensionRubricLine
    feasibility: DimensionRubricLine
    evidence_strength: DimensionRubricLine
    penalties: list[str]
    weighted_total: float = Field(default=0.0, ge=0, le=10)


class UseCaseGrade(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case_id: str
    strengths: list[str] = Field(..., min_length=1)
    weaknesses: list[str] = Field(..., min_length=1)
    rationale: str
    company_relevance: DimensionRubricLine
    business_impact: DimensionRubricLine
    iconicness: DimensionRubricLine
    genai_fit: DimensionRubricLine
    feasibility: DimensionRubricLine
    evidence_strength: DimensionRubricLine
    penalties: list[str]


class SingleUseCaseGradeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grader_thinking: str = Field(
        ...,
        min_length=1,
        description=(
            "Single-use-case skepticism and replaceability analysis before the "
            "grade. Not for client reports."
        ),
    )
    grade: UseCaseGrade


class GradedUseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: GenAIUseCaseCandidate
    score: UseCaseScore


class GradedUseCasePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grader_thinking: str = Field(
        ...,
        min_length=1,
        description="Echo of internal grader pre-analysis. Not for client reports.",
    )
    graded_use_cases: list[GradedUseCase] = Field(..., min_length=1)


class FinalSelectionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected: list[GradedUseCase] = Field(..., min_length=3, max_length=3)


class GradeSingleUseCaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    use_case: GenAIUseCaseCandidate
    peer_summaries: list[str]


class GenAIUseCaseCandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput


class PipelineOutput(BaseModel):
    id: int
    kind: Literal["text", "json"]
    text: str | None = None
    data: dict[str, Any] | None = None


class MarkdownReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    final_selection: FinalSelectionOutput


class MarkdownReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str


class SparkstralWorkflowResult(BaseModel):
    outputs: list[PipelineOutput]
    final: str
