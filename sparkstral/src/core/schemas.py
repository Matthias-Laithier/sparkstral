from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., description="Raw company name entered by the user.")


class ResearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_query: str


class ResearchResult(BaseModel):
    text: str


class CompanyProfileOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
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
    genai_vs_classical: str = Field(
        ...,
        description=(
            "One paragraph: what GenAI adds beyond classical software and ML, "
            "what classical systems still handle well, and where the human "
            "decision point remains."
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
    baseline_source: str = Field(
        ...,
        description=(
            "What baseline measurement is needed before the pilot. Do not state "
            "a current value unless it comes from evidence_sources; write "
            "'not yet measured' otherwise."
        ),
    )


class GenAIUseCaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    business_domain: str = Field(
        ...,
        min_length=1,
        description=(
            "Short snake_case label for the company business division or function "
            "this use case belongs to. Two use cases that address the same underlying "
            "business process must share the same label even if they reference "
            "different products or platforms."
        ),
    )
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
    required_data: list[str] = Field(
        ...,
        min_length=1,
        description="Data sources and system integrations needed, one item per entry.",
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


class FactCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    use_case: GenAIUseCaseCandidate


class FactCheckOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corrections_planned: list[str] = Field(
        ...,
        description=(
            "List each factual error found and how you will fix it, "
            "before writing the corrected fields. Empty list if nothing to fix."
        ),
    )
    business_problem: str
    genai_solution: str
    why_this_company: str
    why_iconic: str
    feasibility_notes: str
    required_data: list[str] = Field(
        ..., min_length=1, description="Corrected data/integration needs."
    )


class MoatAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    moat_name: str = Field(
        ..., description="Named company asset, acquisition, platform, or initiative."
    )
    source_url: str = Field(..., description="URL from the research backing this moat.")
    genai_angle: str = Field(
        ...,
        description="One sentence: non-obvious way GenAI could exploit this moat.",
    )
    assigned_domain: str = Field(
        ...,
        min_length=1,
        description="Snake_case business domain this moat targets.",
    )
    suggested_approach: str = Field(
        ...,
        description=(
            "Free-text description of the GenAI workflow direction — input "
            "modalities, reasoning pattern, and output type."
        ),
    )


class IdeationBrief(BaseModel):
    """Output of the ideation agent: 5 moat assignments for parallel generation."""

    model_config = ConfigDict(extra="forbid")

    rejected_obvious_ideas: list[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3-5 first-order GenAI ideas rejected for being industry-generic.",
    )
    assignments: list[MoatAssignment] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Exactly 5 moat assignments with diverse domains and approaches.",
    )


class IdeationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput


class SingleUseCaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    assignment: MoatAssignment
    peer_assignments: list[MoatAssignment]
    use_case_index: int = Field(
        ..., ge=1, le=5, description="1-based index for use case ID (uc_1..uc_5)."
    )


class SingleUseCaseGeneration(BaseModel):
    """Output of one parallel use-case generator."""

    model_config = ConfigDict(extra="forbid")

    use_case: GenAIUseCaseCandidate


class MarkdownReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_profile: CompanyProfileOutput
    final_selection: FinalSelectionOutput


class ReportNarratives(BaseModel):
    """LLM-generated prose sections that cannot be programmatically templated."""

    model_config = ConfigDict(extra="forbid")

    company_context: str = Field(
        ...,
        description=(
            "2 paragraphs: lead with the most recent and strategically significant "
            "developments, then summarize business lines and competitive position."
        ),
    )
    opportunity_blurbs: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description=(
            "One paragraph per selected use case (in rank order): weave together "
            "the business problem, company fit, and what makes it iconic."
        ),
    )
    decision_rationales: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description=(
            "One sentence per selected use case (in rank order) for the summary "
            "table: what is distinctive about this opportunity."
        ),
    )
    limitations: list[str] = Field(
        ...,
        min_length=2,
        max_length=3,
        description=(
            "2-3 specific data gaps or assumptions: missing internal data, "
            "unverified timelines, press-release-only figures."
        ),
    )


class MarkdownReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str


class SparkstralWorkflowResult(BaseModel):
    final: str
