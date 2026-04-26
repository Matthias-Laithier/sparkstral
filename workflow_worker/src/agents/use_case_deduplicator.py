from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import (
    use_case_deduplicator_system_prompt,
    use_case_deduplicator_user_prompt,
)
from src.schemas import (
    DeduplicateUseCasesInput,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidatePool,
    UseCaseDeduplicationOutput,
)
from src.utils import parse_chat_model


def build_deduplicated_use_case_pool(
    deduplication: UseCaseDeduplicationOutput,
    use_cases: list[GenAIUseCaseCandidate],
) -> GenAIUseCaseCandidatePool:
    input_ids = [use_case.id for use_case in use_cases]
    retained_ids = deduplication.retained_use_case_ids

    if len(set(retained_ids)) != len(retained_ids):
        raise ValueError("deduplicator returned duplicate use case IDs")
    for id in retained_ids:
        if id not in input_ids:
            raise ValueError(f"deduplicator returned unknown use case ID: {id}")

    return GenAIUseCaseCandidatePool(
        use_cases=[use_case for use_case in use_cases if use_case.id in retained_ids]
    )


class UseCaseDeduplicatorAgent(
    BaseAgent[DeduplicateUseCasesInput, GenAIUseCaseCandidatePool]
):
    name = "use-case-deduplicator"

    async def run(
        self,
        params: DeduplicateUseCasesInput,
    ) -> GenAIUseCaseCandidatePool:
        result = await parse_chat_model(
            self.client,
            UseCaseDeduplicationOutput,
            phase="use-case deduplication",
            model=settings.DEDUPLICATOR_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": use_case_deduplicator_system_prompt()},
                {
                    "role": "user",
                    "content": use_case_deduplicator_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.use_cases,
                    ),
                },
            ],
        )
        return build_deduplicated_use_case_pool(result, params.use_cases)
