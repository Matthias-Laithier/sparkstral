from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.schemas import IdeationBrief, IdeationInput
from src.llm import parse_chat_model
from src.prompts.generation import ideation_system_prompt, ideation_user_prompt


class IdeationAgent(BaseAgent[IdeationInput, IdeationBrief]):
    name = "ideation"

    async def run(self, params: IdeationInput) -> IdeationBrief:
        return await parse_chat_model(
            self.client,
            IdeationBrief,
            phase="ideation brief",
            model=settings.GENAI_USE_CASES_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.GENAI_USE_CASES_LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": ideation_system_prompt()},
                {
                    "role": "user",
                    "content": ideation_user_prompt(params.company_profile),
                },
            ],
        )
