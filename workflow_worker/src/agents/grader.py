from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.schemas import (
    CompanyProfileOutput,
    GenAIUseCaseCandidate,
    GradedUseCase,
    GradedUseCasePool,
    GradeSingleUseCaseInput,
    SingleUseCaseGradeResult,
    UseCaseScore,
)
from src.llm import parse_chat_model
from src.prompts import grade_single_use_case_user_prompt, use_case_grader_system_prompt


def compute_weighted_total(score: UseCaseScore) -> float:
    return round(
        0.25 * score.iconicness.score
        + 0.25 * score.genai_fit.score
        + 0.20 * score.business_impact.score
        + 0.15 * score.company_relevance.score
        + 0.08 * score.feasibility.score
        + 0.07 * score.evidence_strength.score,
        2,
    )


def build_single_use_case_grade_inputs(
    company_profile: CompanyProfileOutput,
    use_cases: list[GenAIUseCaseCandidate],
) -> list[GradeSingleUseCaseInput]:
    peer_map = {
        use_case.id: f"{use_case.id}: {use_case.title} — {use_case.business_problem}"
        for use_case in use_cases
    }
    if len(peer_map) != len(use_cases):
        raise ValueError("generated use cases contain duplicate IDs")

    return [
        GradeSingleUseCaseInput(
            company_profile=company_profile,
            use_case=use_case,
            peer_summaries=[
                summary
                for peer_id, summary in peer_map.items()
                if peer_id != use_case.id
            ],
        )
        for use_case in use_cases
    ]


def build_graded_use_case_pool(
    use_cases: list[GenAIUseCaseCandidate],
    single_grades: list[SingleUseCaseGradeResult],
) -> GradedUseCasePool:
    graded_items: list[GradedUseCase] = []
    grader_thinking_lines: list[str] = []
    for use_case, result in zip(use_cases, single_grades, strict=True):
        if result.grade.use_case_id != use_case.id:
            raise ValueError(
                "single-use-case grader returned use case ID "
                f"{result.grade.use_case_id} for {use_case.id}"
            )

        score = UseCaseScore(**result.grade.model_dump())
        score.weighted_total = compute_weighted_total(score)
        graded_items.append(GradedUseCase(use_case=use_case, score=score))
        grader_thinking_lines.append(
            f"{result.grade.use_case_id}: {result.grader_thinking}"
        )

    return GradedUseCasePool(
        grader_thinking="\n".join(grader_thinking_lines),
        graded_use_cases=graded_items,
    )


class SingleUseCaseGraderAgent(
    BaseAgent[GradeSingleUseCaseInput, SingleUseCaseGradeResult],
):
    name = "single-use-case-grader"

    async def run(self, params: GradeSingleUseCaseInput) -> SingleUseCaseGradeResult:
        result = await parse_chat_model(
            self.client,
            SingleUseCaseGradeResult,
            phase="use-case grading",
            model=settings.USE_CASE_GRADER_AGENT_MODEL,
            max_tokens=settings.GRADER_LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": use_case_grader_system_prompt()},
                {
                    "role": "user",
                    "content": grade_single_use_case_user_prompt(
                        params.company_profile,
                        params.use_case,
                        params.peer_summaries,
                    ),
                },
            ],
        )
        if result.grade.use_case_id != params.use_case.id:
            raise ValueError(
                "grader returned use case ID "
                f"{result.grade.use_case_id} for {params.use_case.id}"
            )
        return result
