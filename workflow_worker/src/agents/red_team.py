from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import red_team_system_prompt, red_team_user_prompt
from src.schemas import RedTeamInput, RedTeamOutput
from src.utils import parse_chat_model


class RedTeamAgent(BaseAgent[RedTeamInput, RedTeamOutput]):
    name = "red-team"

    async def run(self, params: RedTeamInput) -> RedTeamOutput:
        result = await parse_chat_model(
            self.client,
            RedTeamOutput,
            phase="red-team review",
            model=settings.RED_TEAM_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": red_team_system_prompt()},
                {
                    "role": "user",
                    "content": red_team_user_prompt(
                        params.company_profile,
                        params.pain_points,
                        params.opportunity_map,
                        params.selected_use_cases,
                    ),
                },
            ],
        )
        selected_ids = sorted(item.use_case.id for item in params.selected_use_cases)
        review_ids = sorted(review.use_case_id for review in result.reviews)
        if review_ids != selected_ids:
            raise RuntimeError(
                "red-team review must include exactly one review per selected use case"
            )
        return result
