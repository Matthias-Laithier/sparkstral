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
        "summarization, route optimization, generic dashboards). Also reject "
        "second-order obvious ideas: risk assessment dashboards, compliance "
        "report generators, proposal automation, document Q&A systems, and "
        "anything that reduces to 'ingest documents, synthesize, output "
        "report.' These are table-stakes GenAI patterns, not differentiators. "
        "Name each rejected idea in one short phrase — no explanation "
        "needed.\n\n"
        "STEP 2 — MOAT ASSIGNMENTS:\n"
        "Identify exactly 5 unique company moats from the research — named "
        "assets, recent acquisitions, proprietary platforms, exclusive "
        "partnerships, scale facts, or regulatory positions. For each moat:\n"
        "- `moat_name`: the specific company asset or fact\n"
        "- `source_url`: the URL from the research backing this moat\n"
        "- `genai_angle`: one sentence describing a non-obvious way GenAI could "
        "exploit it — non-obvious means a domain expert would say 'I hadn't "
        "thought of using that asset for that purpose.' If the connection "
        "between moat and application is immediately obvious, the angle is "
        "not creative enough. Rethink who the user is, what the output "
        "artifact is, or what problem it solves\n"
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
        "- Each `suggested_approach` must name a distinct output artifact "
        "that the GenAI system produces. No two assignments may share the "
        "same output type. Example output types: 'a structured proposal "
        "document', 'a voice briefing for branch staff', 'an annotated "
        "compliance report', 'an interactive training scenario', 'a visual "
        "coverage map with annotations'. If two approaches would produce "
        "the same kind of document, rewrite one to deliver a different "
        "artifact.\n"
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
        "research. Write `why_this_company` as: 'This requires [specific "
        "company fact]. Competitors cannot easily replicate because [concrete "
        "reason].' Prefer tying the use case to events from the last "
        "12 months when possible.\n\n"
        "QUALITY GATES:\n"
        "GenAI must add value through messy language, documents, images, "
        "conflicting context, retrieval with reasoning, tool use, structured "
        "drafting, or human-reviewable decisions. Frame GenAI outputs as "
        "recommendations, decision briefs, or human-approved action plans. "
        "GenAI retrieves, synthesizes, drafts, and proposes — for "
        "deterministic computation, describe GenAI as calling an external "
        "tool.\n"
        "Reject if the core workflow reduces to 'ingest documents, "
        "synthesize, output a report or recommendation.' This is the default "
        "GenAI pattern and is not a differentiator. Also reject: chatbots, "
        "dashboards, generic document summarization, automated report "
        "generation, route optimization, and predictive maintenance with a "
        "GenAI label.\n\n"
        "SURPRISE TEST:\n"
        "Strip the company name and product names from this use case. Does "
        "it still feel specific and interesting, or does it collapse into a "
        "generic pattern any company could use? If the latter, start over "
        "with a different angle on the moat.\n\n"
        "FIELD GUIDANCE:\n"
        "For `genai_solution`, describe what goes in, what the GenAI system "
        "does, and what comes out. Stay at workflow level — do not specify "
        "file formats, UI technologies, or implementation details the "
        "research cannot confirm.\n"
        "For `genai_vs_classical`, write one paragraph on what GenAI adds, "
        "what classical systems still handle, and where the human decision "
        "point remains.\n"
        "Each pilot KPI: what to measure, why, measurement method, target "
        "direction. Set `baseline_source` to a source URL or 'not yet "
        "measured'. `source_backed_metrics` is empty unless directly "
        "sourced.\n\n"
        "GROUNDING:\n"
        "Every fact, number, date, product name, and capability must trace "
        "to the research text. If it is not in the research, do not write "
        "it — use 'to be confirmed with client' instead. Do not reference "
        "discontinued products as active. Use the exact stage the source "
        "describes for M&A, partnerships, and launches. Do not invent "
        "internal datasets, proprietary models, or access to external APIs "
        "the research does not confirm.\n\n"
        "TARGET USERS:\n"
        "The `target_users` must match the business division or customer "
        "segment the research describes for the relevant product or service."
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
        "that input.\n\n"
        "TITLE DIVERSITY: Check the peer assignments. Do not reuse a "
        "structure word that a peer's suggested_approach implies (e.g., if "
        "a peer suggests 'scenario generation', do not name yours "
        "'X Scenario Generator'). Vary the title shape — use different "
        "patterns like '[Asset] [Action] for [Users]', '[Verb]-based "
        "[Noun] for [Context]', or '[Domain] [Deliverable] from [Input]'."
    )
