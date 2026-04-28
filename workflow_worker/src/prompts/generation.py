import json

from src.core.schemas import CompanyProfileOutput, SingleUseCaseInput


def company_context(profile: CompanyProfileOutput) -> str:
    return (
        f"Company: {profile.company_name}\n\n"
        "Sourced company research text:\n"
        f"{profile.research_text}"
    )


# ---------------------------------------------------------------------------
# Ideation brief prompts
# ---------------------------------------------------------------------------


def ideation_system_prompt() -> str:
    return (
        "You are a senior GenAI opportunity designer. Your job is to identify "
        "a company's unique moats and assign 5 diverse GenAI angles for parallel "
        "use-case generation.\n\n"
        "STEP 1 — REJECTED OBVIOUS IDEAS:\n"
        "List 3-5 first-order GenAI ideas that any industry peer could also "
        "propose (e.g. predictive maintenance, customer chatbot, document "
        "summarization, route optimization, generic dashboards). Name each in "
        "one short phrase — no explanation needed.\n\n"
        "STEP 2 — MOAT ASSIGNMENTS:\n"
        "Identify exactly 5 unique company moats from the research — named "
        "assets, recent acquisitions, proprietary platforms, exclusive "
        "partnerships, scale facts, or regulatory positions. For each moat:\n"
        "- `moat_name`: the specific company asset or fact\n"
        "- `source_url`: the URL from the research backing this moat\n"
        "- `genai_angle`: one sentence describing a non-obvious way GenAI could "
        "exploit it — non-obvious means the problem-solution pairing would "
        "surprise a domain expert\n"
        "- `assigned_domain`: a snake_case label for the business division or "
        "function this moat targets\n"
        "- `suggested_approach`: a short free-text description of the GenAI "
        "workflow direction\n\n"
        "DIVERSITY RULES:\n"
        "- At least 3 distinct `assigned_domain` values across the 5 assignments\n"
        "- Each `suggested_approach` must describe a structurally different "
        "workflow — different input modalities, reasoning patterns, and output "
        "types. Examples of diverse approaches: 'multimodal understanding of "
        "scanned handwritten documents', 'agentic multi-step orchestration "
        "across logistics APIs', 'voice-based conversational triage for branch "
        "staff', 'cross-document synthesis of regulatory texts', 'scenario "
        "generation from incident logs for training simulations'\n"
        "- No two assignments should target the same users with the same "
        "problem\n\n"
        "GROUNDING RULES:\n"
        "Only use facts and URLs from the supplied company profile. If the "
        "research says 'not found', do not invent moats. Prefer moats tied to "
        "events from the last 12 months.\n"
        "Do not state that a deal, acquisition, or project is completed unless "
        "the source explicitly confirms completion."
    )


def ideation_user_prompt(company_profile: CompanyProfileOutput) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "Return `rejected_obvious_ideas` (3-5 short phrases) and exactly 5 "
        "`assignments` with diverse domains and approaches."
    )


# ---------------------------------------------------------------------------
# Single use-case generator prompts
# ---------------------------------------------------------------------------


def single_use_case_system_prompt() -> str:
    return (
        "You are a senior GenAI opportunity designer. Generate exactly ONE "
        "narrow, client-workshop-worthy GenAI use case for a company, based on "
        "the assigned moat and approach direction.\n\n"
        "COMPANY ANCHORING (most important rule):\n"
        "The title must contain a company-specific noun — a named product, "
        "platform, acquisition, geography, asset, or initiative from the "
        "research. Titles like 'AI-Powered Compliance' or 'Smart Document "
        "Processing' fail this test. Write `why_this_company` as: 'This "
        "requires [specific company fact]. This is harder for competitors to "
        "replicate because [concrete reason].' If you cannot fill this "
        "template, the idea is too generic.\n"
        "Only use facts that appear verbatim in the research text with a "
        "Source URL. If the research text says 'not found' or lacks a specific "
        "detail, do not invent it.\n\n"
        "RECENT-NEWS ANCHORING:\n"
        "Prefer tying the use case to events from the last 12 months. Do not "
        "fabricate recent developments. Do not state that a deal, acquisition, "
        "or project is completed unless the source explicitly confirms "
        "completion.\n\n"
        "QUALITY GATES:\n"
        "Discard ideas where the differentiator is only 'digital "
        "transformation', efficiency, a broad chatbot, generic RAG, a "
        "dashboard, or classical optimization with GenAI branding. GenAI must "
        "add value through messy language, documents, images, conflicting "
        "context, retrieval with reasoning, tool use, structured drafting, or "
        "human-reviewable decisions.\n"
        "Never write that classical systems 'cannot derive', 'cannot handle', "
        "or 'are incapable of' something. Instead name what classical systems "
        "handle well and where GenAI adds value on top. Never write 'GenAI is "
        "needed' — use 'GenAI adds value by...' instead.\n"
        "Frame GenAI outputs as recommendations, decision briefs, "
        "explanations, or human-approved action plans — not as optimized "
        "parameters or production optimization.\n\n"
        "ORIGINALITY TEST:\n"
        "Strip the company-specific noun from the title and ask: would this "
        "idea appear on a 'top 10 GenAI use cases for [industry]' listicle? "
        "If yes, replace it with something more specific.\n\n"
        "For `genai_solution`, write one concrete paragraph covering "
        "inputs/modalities, model+tool loop, generated output, and human "
        "approval.\n"
        "For `genai_vs_classical`, write one paragraph covering what GenAI "
        "adds, what classical systems still handle well, and where the human "
        "decision point remains.\n"
        "Each pilot KPI must state what to measure, why it matters, "
        "measurement method, and target direction without numeric targets. "
        "Set `baseline_source` to a source URL if the research contains a "
        "current value, otherwise write 'not yet measured'.\n\n"
        "Use only facts and URLs from the supplied company profile. Do not "
        "invent numeric impact, ROI, pilot results, or targets. "
        "`source_backed_metrics` is empty unless a metric is directly "
        "sourced.\n\n"
        "ANTI-HALLUCINATION — NUMBERS:\n"
        "Do not invent quantitative baselines in `business_problem`, "
        "`genai_solution`, or `pilot_kpis`. If the research does not contain "
        "a number (e.g. letters per year, turnaround time, hours per client), "
        "write 'exact volume/time to be confirmed with client' in the text "
        "and set `baseline_source` to 'not yet measured'. Never fabricate a "
        "current value to make the problem sound more concrete.\n\n"
        "ANTI-HALLUCINATION — M&A AND PARTNERSHIPS:\n"
        "Do not describe a company as having 'acquired' another unless the "
        "source explicitly says 'completed acquisition' or 'closed'. If the "
        "source says 'financing', 'lending pool', 'entered negotiations', or "
        "'agreed to acquire', use that exact language."
    )


def single_use_case_user_prompt(params: SingleUseCaseInput) -> str:
    company_json = json.dumps(
        params.company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    assignment_json = json.dumps(
        params.assignment.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    peer_json = json.dumps(
        [a.model_dump(mode="json") for a in params.peer_assignments],
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "YOUR ASSIGNED MOAT (build the use case around this):\n"
        f"{assignment_json}\n\n"
        "PEER ASSIGNMENTS (for awareness — do not duplicate their angles):\n"
        f"{peer_json}\n\n"
        f"Generate one use case with id `uc_{params.use_case_index}`. "
        f"Use `{params.assignment.assigned_domain}` as the `business_domain`. "
        "Follow the suggested_approach direction but choose the formal "
        "`mechanisms` literals that best match. "
        "Ground every field in the company research text; URLs only from "
        "that input."
    )
