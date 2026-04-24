import json
import logging

from src.core.config import settings
from src.workflow.agents.base import BaseAgent
from src.workflow.schemas import (
    GenAIUseCasesInput,
    GenAIUseCasesOutput,
)

logger = logging.getLogger(__name__)


class GenAIUseCasesAgent(BaseAgent):
    name = "genai-use-cases"
    system_prompt = (
        "You are a principal GenAI strategy consultant. You receive a structured"
        " company profile and a structured pain-point analysis. Propose 8-12 (aim"
        " for 10) high-impact, company-specific generative-AI use cases that feel"
        " iconic for THIS company—not interchangeable with any other business.\n"
        "Each use case must tie to the company profile, pain points, industry, and"
        " strategic priorities. Be concrete: name workflows, data, org roles, and"
        " what makes the solution distinctive.\n"
        "STRICT: Do not propose overused, generic product ideas, including: generic"
        " customer support chatbot, internal knowledge assistant or RAG for documents,"
        " or generic marketing copy generators, unless the write-up is so specific to"
        " this company that it is clearly not a default listing.\n"
        "Prefer creative combinations of agents, tools, and domain control that"
        " plausibly use this org's data and market position. Vary angles across the"
        " list (e.g."
        " operations, product, risk, R&D, partner ecosystem) where relevant."
    )

    async def run(self, input: GenAIUseCasesInput) -> GenAIUseCasesOutput:  # type: ignore[override]
        company_json = json.dumps(
            input.company_profile.model_dump(mode="json"), indent=2, ensure_ascii=False
        )
        pain_json = json.dumps(
            input.pain_points.model_dump(mode="json"), indent=2, ensure_ascii=False
        )
        try:
            parsed = await self.client.chat.parse_async(
                GenAIUseCasesOutput,
                model=settings.GENAI_USE_CASES_MODEL,
                temperature=settings.GENAI_USE_CASES_TEMPERATURE,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Company profile (JSON):\n"
                            f"{company_json}\n\n"
                            "Pain point analysis (JSON):\n"
                            f"{pain_json}\n\n"
                            "Output exactly 8-12 use cases. Each must have: title; "
                            "target_users (1+); business_problem; why_this_company; "
                            "genai_solution; required_data; expected_impact;"
                            " risks (1+)."
                        ),
                    },
                ],
            )
        except Exception:
            logger.exception("GenAI use cases generation failed")
            return GenAIUseCasesOutput()
        if (
            parsed.choices
            and parsed.choices[0].message
            and parsed.choices[0].message.parsed is not None
        ):
            return parsed.choices[0].message.parsed
        return GenAIUseCasesOutput()
