"""Lightweight test factories for building schema objects with minimal boilerplate."""

from src.core.schemas import (
    CompanyProfileOutput,
    DimensionRubricLine,
    FinalSelectionOutput,
    GenAIMechanism,
    GenAIUseCaseCandidate,
    GradedUseCase,
    PilotKPI,
    SingleUseCaseGradeResult,
    UseCaseGrade,
    UseCaseScore,
)


def make_line(score: int = 5, rationale: str = "ok") -> DimensionRubricLine:
    return DimensionRubricLine(rationale=rationale, score=score)


def make_score(
    use_case_id: str,
    *,
    iconicness: int = 5,
    genai_fit: int = 5,
    business_impact: int = 5,
    company_relevance: int = 5,
    feasibility: int = 5,
    evidence_strength: int = 5,
    weighted_total: float | None = None,
) -> UseCaseScore:
    score = UseCaseScore(
        use_case_id=use_case_id,
        strengths=["s"],
        weaknesses=["w"],
        rationale="r",
        company_relevance=make_line(company_relevance),
        business_impact=make_line(business_impact),
        iconicness=make_line(iconicness),
        genai_fit=make_line(genai_fit),
        feasibility=make_line(feasibility),
        evidence_strength=make_line(evidence_strength),
        penalties=[],
    )
    if weighted_total is not None:
        score.weighted_total = weighted_total
    return score


def make_candidate(
    index: int,
    *,
    domain: str = "default",
    signals: list[str] | None = None,
) -> GenAIUseCaseCandidate:
    return GenAIUseCaseCandidate(
        id=f"uc_{index}",
        title=f"Use case {index}",
        business_domain=domain,
        target_users=["user"],
        business_problem=f"Problem {index}",
        why_this_company="Fits.",
        genai_solution="Solution.",
        genai_mechanism=GenAIMechanism(
            mechanisms=["retrieval_augmented_generation"],
            why_genai_is_needed="needed",
            genai_advantage_over_classical_software="advantage sw",
            genai_advantage_over_classical_ml="advantage ml",
        ),
        required_data="data",
        qualitative_impact="impact",
        source_backed_metrics=[],
        pilot_kpis=[
            PilotKPI(
                kpi="KPI A",
                why_it_matters="matters",
                measurement_method="method",
                target_direction="increase",
                baseline_needed="baseline",
            ),
            PilotKPI(
                kpi="KPI B",
                why_it_matters="matters",
                measurement_method="method",
                target_direction="decrease",
                baseline_needed="baseline",
            ),
        ],
        why_iconic="iconic",
        feasibility_notes="feasible",
        risks=["risk"],
        company_signal_labels=signals or [f"signal_{index}"],
        evidence_sources=["https://example.com"],
    )


def make_graded(
    index: int,
    *,
    weighted_total: float = 5.0,
    domain: str = "default",
    signals: list[str] | None = None,
) -> GradedUseCase:
    return GradedUseCase(
        use_case=make_candidate(index, domain=domain, signals=signals),
        score=make_score(f"uc_{index}", weighted_total=weighted_total),
    )


def make_grade(use_case_id: str, **dim_overrides: int) -> UseCaseGrade:
    dims = {
        "company_relevance": 5,
        "business_impact": 5,
        "iconicness": 5,
        "genai_fit": 5,
        "feasibility": 5,
        "evidence_strength": 5,
    }
    dims.update(dim_overrides)
    return UseCaseGrade(
        use_case_id=use_case_id,
        strengths=["s"],
        weaknesses=["w"],
        rationale="r",
        penalties=[],
        **{k: make_line(v) for k, v in dims.items()},
    )


def make_grade_result(
    use_case_id: str, **dim_overrides: int
) -> SingleUseCaseGradeResult:
    return SingleUseCaseGradeResult(
        grader_thinking=f"Thinking for {use_case_id}",
        grade=make_grade(use_case_id, **dim_overrides),
    )


def make_profile() -> CompanyProfileOutput:
    return CompanyProfileOutput(
        company_name="Acme",
        research_text="Acme is a manufacturing company.",
    )


def make_final_selection(count: int = 3) -> FinalSelectionOutput:
    return FinalSelectionOutput(
        selected=[make_graded(i, weighted_total=8.0 - i) for i in range(1, count + 1)]
    )
