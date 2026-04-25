from src.agents.base import BaseAgent
from src.config import settings
from src.prompts import opportunity_mapper_system_prompt, opportunity_mapper_user_prompt
from src.schemas import OpportunityMapInput, OpportunityMapOutput
from src.utils import parse_chat_model


class OpportunityMapperAgent(BaseAgent[OpportunityMapInput, OpportunityMapOutput]):
    name = "opportunity-mapper"

    async def run(self, params: OpportunityMapInput) -> OpportunityMapOutput:
        return await parse_chat_model(
            self.client,
            OpportunityMapOutput,
            phase="opportunity mapping",
            model=settings.OPPORTUNITY_MAPPER_AGENT_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": opportunity_mapper_system_prompt()},
                {
                    "role": "user",
                    "content": opportunity_mapper_user_prompt(
                        params.company_profile,
                        params.pain_points,
                    ),
                },
            ],
        )
