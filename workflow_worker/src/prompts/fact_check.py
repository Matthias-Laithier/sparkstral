import json

from src.core.schemas import (
    CompanyProfileOutput,
    GenAIUseCaseCandidate,
    ReportNarratives,
)

# ---------------------------------------------------------------------------
# Use-case fact-check prompts
# ---------------------------------------------------------------------------


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
        "it or replace it with what the research actually says.\n"
        "- If a product name, brand, technology, platform, or subsidiary is "
        "mentioned that does not appear anywhere in the research text, remove "
        "it or replace it with what the research does say.\n\n"
        "Preserve the use case's overall direction, tone, and structure. "
        "Do not rewrite from scratch — make targeted corrections only.\n"
        "Do not remove or soften creative solution designs, novel workflow "
        "concepts, or innovative user targeting. These are design choices, "
        "not factual claims. Only correct claims about what the company "
        "owns, has achieved, or currently operates.\n"
        "First, list every error you found in `corrections_planned` — state "
        "what is wrong and how you will fix it. Then write the corrected "
        "fields. If nothing needs fixing, return an empty list and the "
        "fields unchanged."
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
        "First return corrections_planned listing each error and its fix. "
        "Then return corrected versions of: business_problem, genai_solution, "
        "why_this_company, why_iconic, feasibility_notes, required_data."
    )


# ---------------------------------------------------------------------------
# Narrative fact-check prompts
# ---------------------------------------------------------------------------


def fact_check_narratives_system_prompt() -> str:
    return (
        "You are a fact-checker for the prose sections of a GenAI opportunity "
        "report. You receive company_context and opportunity_blurbs along "
        "with the research text they must be grounded in.\n\n"
        "Compare every factual claim against the research text:\n"
        "- Correct wrong numbers, dates, or financial figures.\n"
        "- Remove or correct references to discontinued products, brands, "
        "or subsidiaries that the research says are no longer active.\n"
        "- Remove product names, technologies, or platforms that do not "
        "appear in the research text.\n"
        "- Preserve the writing style, structure, and length. Make targeted "
        "corrections only — do not rewrite from scratch.\n"
        "First, list every error you found in `corrections_planned` — state "
        "what is wrong and how you will fix it. Then write the corrected "
        "fields. If nothing needs fixing, return an empty list and the "
        "fields unchanged."
    )


def fact_check_narratives_user_prompt(
    company_profile: CompanyProfileOutput,
    narratives: ReportNarratives,
) -> str:
    return (
        "RESEARCH TEXT:\n"
        f"{company_profile.research_text}\n\n"
        "COMPANY CONTEXT TO FACT-CHECK:\n"
        f"{narratives.company_context}\n\n"
        "OPPORTUNITY BLURBS TO FACT-CHECK:\n"
        + "\n\n".join(
            f"[{i + 1}] {blurb}"
            for i, blurb in enumerate(narratives.opportunity_blurbs)
        )
        + "\n\nReturn corrected company_context, opportunity_blurbs (in the "
        "same order), and corrections_planned."
    )
