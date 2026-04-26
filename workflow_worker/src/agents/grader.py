from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import use_case_grader_system_prompt, use_case_grader_user_prompt
from src.schemas import (
    GenAIUseCaseCandidate,
    GradedUseCase,
    GradedUseCasePool,
    GradeUseCasesInput,
    UseCaseGrade,
    UseCaseGradePool,
    UseCaseScore,
)
from src.utils import parse_chat_model


def compute_weighted_total(score: UseCaseScore) -> float:
    return round(
        0.40 * score.iconicness
        + 0.25 * score.business_impact
        + 0.15 * score.genai_fit
        + 0.10 * score.company_relevance
        + 0.05 * score.feasibility
        + 0.05 * score.evidence_strength,
        2,
    )


def build_graded_use_cases(
    grades: list[UseCaseGrade],
    use_cases: list[GenAIUseCaseCandidate],
) -> list[GradedUseCase]:
    use_case_by_id: dict[str, GenAIUseCaseCandidate] = {}
    duplicate_input_ids: set[str] = set()
    for use_case in use_cases:
        if use_case.id in use_case_by_id:
            duplicate_input_ids.add(use_case.id)
        use_case_by_id[use_case.id] = use_case

    if duplicate_input_ids:
        raise ValueError(
            "duplicate input use case IDs: " + ", ".join(sorted(duplicate_input_ids))
        )

    seen_grade_ids: set[str] = set()
    graded_use_cases: list[GradedUseCase] = []
    for grade in grades:
        if grade.use_case_id in seen_grade_ids:
            raise ValueError(
                f"grader returned duplicate use case ID: {grade.use_case_id}"
            )
        seen_grade_ids.add(grade.use_case_id)

        matched_use_case = use_case_by_id.get(grade.use_case_id)
        if matched_use_case is None:
            raise ValueError(
                f"grader returned unknown use case ID: {grade.use_case_id}"
            )

        score = UseCaseScore(**grade.model_dump(), weighted_total=1.0)
        graded_use_cases.append(
            GradedUseCase(
                use_case=matched_use_case,
                score=score.model_copy(
                    update={"weighted_total": compute_weighted_total(score)}
                ),
            )
        )

    missing_ids = [
        use_case.id for use_case in use_cases if use_case.id not in seen_grade_ids
    ]
    if missing_ids:
        raise ValueError(
            "grader did not return grades for use case IDs: " + ", ".join(missing_ids)
        )

    return graded_use_cases


class UseCaseGraderAgent(BaseAgent[GradeUseCasesInput, GradedUseCasePool]):
    name = "use-case-grader"

    async def run(self, params: GradeUseCasesInput) -> GradedUseCasePool:
        result = await parse_chat_model(
            self.client,
            UseCaseGradePool,
            phase="use-case grading",
            model=settings.USE_CASE_GRADER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": use_case_grader_system_prompt()},
                {
                    "role": "user",
                    "content": use_case_grader_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.use_cases,
                    ),
                },
            ],
        )
        return GradedUseCasePool(
            graded_use_cases=build_graded_use_cases(result.grades, params.use_cases)
        )
