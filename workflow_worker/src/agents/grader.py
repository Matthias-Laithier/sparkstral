from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import use_case_grader_system_prompt, use_case_grader_user_prompt
from src.schemas import (
    GradedUseCase,
    GradedUseCasePool,
    GradeUseCasesInput,
    UseCaseScore,
)
from src.utils import parse_chat_model


def compute_weighted_total(score: UseCaseScore) -> float:
    return round(
        0.25 * score.company_relevance
        + 0.25 * score.business_impact
        + 0.20 * score.genai_fit
        + 0.15 * score.iconicness
        + 0.10 * score.feasibility
        + 0.05 * score.evidence_strength,
        2,
    )


def update_weighted_totals(items: list[GradedUseCase]) -> list[GradedUseCase]:
    return [
        GradedUseCase(
            use_case=item.use_case,
            score=item.score.model_copy(
                update={"weighted_total": compute_weighted_total(item.score)}
            ),
        )
        for item in items
    ]


class UseCaseGraderAgent(BaseAgent[GradeUseCasesInput, GradedUseCasePool]):
    name = "use-case-grader"

    async def run(self, params: GradeUseCasesInput) -> GradedUseCasePool:
        result = await parse_chat_model(
            self.client,
            GradedUseCasePool,
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
            graded_use_cases=update_weighted_totals(result.graded_use_cases)
        )
