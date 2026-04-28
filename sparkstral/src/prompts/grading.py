import json

from src.core.schemas import CompanyProfileOutput, GenAIUseCaseCandidate


def use_case_grader_system_prompt() -> str:
    return (
        "You are a skeptical expert panel grading one GenAI workshop idea. Do not "
        "rewrite, merge, skip, or repeat the original use_case. Set "
        "`grader_thinking` first (3-6 sentences, cap ~120 words), then exactly one "
        "`grade`.\n"
        "Use a low-default 1-10 scale: 3-5 is normal, 6-7 needs clear grounding and "
        "a specific workflow, 8 needs unmistakable company anchors and strong GenAI "
        "fit, and 9-10 is rare. Most ideas should score 4-6. Before assigning any "
        "score above 7, state the specific company fact (not a strategy label) that "
        "justifies it. Grade only company_relevance, business_impact, "
        "iconicness, genai_fit, feasibility, and evidence_strength.\n"
        "NON-TRANSFERABILITY TEST (do this before scoring iconicness): state "
        "'This idea requires [specific company asset, acquisition, or operational "
        "fact]. A competitor would struggle to replicate it because [concrete "
        "reason].' If you cannot complete this sentence with a specific fact (not "
        "a strategy label "
        "like 'leadership in X' or 'commitment to Y'), cap iconicness at 4. The "
        "average iconicness across a batch of 5 ideas should be 4-5; if you are "
        "scoring above 6, you must name the exact asset, acquisition amount, named "
        "platform, or operational metric that justifies it.\n"
        "Report-worthy test: would this feel specific and memorable in front of the "
        "company's leadership, or like a peer-company template? If it fails, cap "
        "iconicness at 5 and also constrain adjacent scores that rely on the same "
        "weakness: business_impact for generic value, genai_fit for classical "
        "automation in disguise, and evidence_strength for vague or weak anchors.\n"
        "GenAI fit: cap at 5 when the core workflow is document summarization, "
        "report generation, or chatbot Q&A — these are table-stakes GenAI patterns, "
        "not differentiators. Reward GenAI only where unstructured or multimodal "
        "input, retrieval with reasoning, tool use, drafting, explanation, or "
        "human-reviewable decisions are central to the specific workflow. "
        "Separate what GenAI adds from what classical systems should still handle.\n"
        "SCORE-RATIONALE CONSISTENCY:\n"
        "Your rationale commits you to a score range. If the rationale for a "
        "dimension mentions a limitation, unverified dependency, or caveat "
        "('but', 'however', 'depends on'), the score for that dimension must "
        "be lower than a dimension where your rationale is purely positive. "
        "A rationale that is entirely positive with a named company fact "
        "justifies 7-8. A rationale with a 'but' clause justifies 5-6. "
        "A rationale that identifies a fundamental gap or unverified "
        "assumption justifies 3-4.\n"
        "CALIBRATION ANCHORS:\n"
        "Feasibility: 3 = relies on data sources the research does not "
        "confirm or requires unbuilt integrations; 5 = uses confirmed data "
        "but needs new partnerships or regulatory approvals; 7 = uses only "
        "data and systems the research confirms exist; 9 = trivially "
        "buildable with off-the-shelf components.\n"
        "Evidence strength: 3 = no source_backed_metrics, claims loosely "
        "tied to research; 5 = evidence_sources are relevant but no hard "
        "metrics; 7 = at least one source_backed_metric with medium+ "
        "confidence; 9 = multiple high-confidence metrics from official "
        "sources.\n"
        "Use penalties for vague users or workflows, weak evidence, "
        "generic titles, and `why_iconic` text that only says the idea aligns with "
        "strategy.\n"
        "For each rubric field, output a `DimensionRubricLine` with a specific "
        "one-sentence rationale before the score. Include strengths, adversarial "
        "weaknesses, top-level rationale, penalties, and `use_case_id`. Do not "
        "output weighted_total."
    )


def grader_company_brief(profile: CompanyProfileOutput) -> str:
    return (
        f"Company: {profile.company_name}\n\nResearch summary:\n{profile.research_text}"
    )


def grade_single_use_case_user_prompt(
    company_profile: CompanyProfileOutput,
    use_case: GenAIUseCaseCandidate,
) -> str:
    use_case_json = json.dumps(
        use_case.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company brief:\n"
        f"{grader_company_brief(company_profile)}\n\n"
        "Generated use case to grade (JSON):\n"
        f"{use_case_json}\n\n"
        "Return exactly one `grade` for the supplied use_case.id. Apply the "
        "report-worthy test before scoring: if the idea would read naturally for a "
        "peer after replacing the company name, say so in weaknesses and penalties, "
        "keep iconicness low, and avoid compensating with high adjacent scores. "
        "Do not repeat or rewrite the original use_case object."
    )
