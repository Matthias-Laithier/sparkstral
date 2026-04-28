import json

from src.core.schemas import CompanyProfileOutput, GenAIUseCaseCandidate


def fact_check_system_prompt() -> str:
    return (
        "You are a fact-checker for a GenAI opportunity report. You receive a "
        "generated use case and the research text it should be grounded in.\n\n"
        "For each free-text field, compare every factual claim against the "
        "research text:\n"
        "- If a claim is directly supported, keep it as-is.\n"
        "- If a claim is plausible but not in the research, soften it: "
        "replace specific details with a high-level description and add "
        "'to be confirmed with client' where appropriate.\n"
        "- If a claim is clearly invented (specific numbers, file formats, "
        "product mechanisms, internal systems not in the research), remove "
        "it or replace it with what the research actually says.\n\n"
        "Preserve the use case's overall direction, tone, and structure. "
        "Do not rewrite from scratch — make targeted corrections only.\n"
        "Do not remove or soften creative solution designs, novel workflow "
        "concepts, or innovative user targeting. These are design choices, "
        "not factual claims. Only correct claims about what the company "
        "owns, has achieved, or currently operates.\n"
        "List every correction you made in `corrections_made`. If nothing "
        "needed fixing, return the fields unchanged with an empty list."
    )


def fact_check_user_prompt(
    company_profile: CompanyProfileOutput,
    use_case: GenAIUseCaseCandidate,
) -> str:
    use_case_json = json.dumps(
        use_case.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "RESEARCH TEXT:\n"
        f"{company_profile.research_text}\n\n"
        "USE CASE TO FACT-CHECK:\n"
        f"{use_case_json}\n\n"
        "Return corrected versions of: business_problem, genai_solution, "
        "why_this_company, why_iconic, feasibility_notes, required_data. "
        "Also return corrections_made listing what you changed and why."
    )
