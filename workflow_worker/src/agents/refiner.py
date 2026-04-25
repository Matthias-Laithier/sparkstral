from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import refiner_system_prompt, refiner_user_prompt
from src.schemas import RefinedUseCasePool, RefineUseCasesInput
from src.utils import parse_chat_model


class UseCaseRefinerAgent(BaseAgent[RefineUseCasesInput, RefinedUseCasePool]):
    name = "use-case-refiner"

    async def run(self, params: RefineUseCasesInput) -> RefinedUseCasePool:
        result = await parse_chat_model(
            self.client,
            RefinedUseCasePool,
            phase="use-case refinement",
            model=settings.REFINER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": refiner_system_prompt()},
                {
                    "role": "user",
                    "content": refiner_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.opportunity_map,
                        params.selected_use_cases,
                        params.red_team,
                    ),
                },
            ],
        )
        selected_by_id = {
            item.use_case.id: item.use_case for item in params.selected_use_cases
        }
        refined_ids = sorted(
            item.original_use_case_id for item in result.refined_use_cases
        )
        selected_ids = sorted(selected_by_id)
        if refined_ids != selected_ids:
            raise RuntimeError(
                "refined use cases must include exactly one item per selected use case"
            )

        for item in result.refined_use_cases:
            original_sources = set(
                selected_by_id[item.original_use_case_id].evidence_sources
            )
            refined_sources = set(item.refined_use_case.evidence_sources)
            if not original_sources.issubset(refined_sources):
                raise RuntimeError(
                    "refined use cases must preserve original evidence source URLs"
                )

        return result
