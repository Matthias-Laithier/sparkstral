import json
from datetime import date
from pathlib import Path

from src.schemas import (
    CompanyProfileOutput,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    UseCaseScore,
)

MARKDOWN_REPORT_TEMPLATE = (
    Path(__file__).parent / "templates" / "genai_use_case_report.md"
).read_text(encoding="utf-8")


def web_search_system_prompt(today: date) -> str:
    return (
        "You are a research assistant. Use web search to find accurate, "
        "up-to-date information. Cite the source URL for every fact you report. "
        "Be concise and to the point. "
        f"The current date is {today:%Y-%m-%d}; use it in searches when recency "
        "matters.\n"
        "ANTI-HALLUCINATION RULES:\n"
        "Every fact you report must come from the search results you received. "
        "Do not supplement with prior knowledge, training data, or common "
        "assumptions.\n"
        "Every URL you cite must be a URL returned by the search tool. Never "
        "construct a URL from a domain name and a guessed path.\n"
        "If a search does not return the information you expected, report that "
        "the information was not found. Do not guess numbers, dates, names, or "
        "amounts.\n"
        "Complete your entire task in one pass. Never ask for confirmation, "
        "permission, or whether you should continue. Execute all requested "
        "steps without stopping."
    )


def combined_research_prompt(company_query: str) -> str:
    return (
        f"Resolve and research this company: {company_query}\n\n"
        "First establish the company identity: find the official company name, "
        "website, headquarters country, primary industry, and note any ambiguity "
        "(similarly named companies, subsidiaries, brands). Use Wikipedia or the "
        "official website. Then immediately proceed to deep research without "
        "stopping — search for the context needed for a GenAI recommendation "
        "workflow. Search for recent developments (last 12 months) first: "
        "acquisitions, earnings results, strategic pivots, new market entries, "
        "major contracts, regulatory changes, and leadership moves. Then cover: "
        "business lines; key customers and segments; named products, platforms, "
        "or proprietary technologies; strategic priorities and initiatives; "
        "geography and markets; operational pain points; regulatory and customer "
        "pressure; growth opportunities; technology and digital transformation "
        "context.\n"
        "Format every finding as: Claim: one concise factual claim; "
        "Source URL: one full http(s) URL. Omit claims without a URL. "
        "Do not invent facts when sources are missing.\n"
        "Prefer sources in this order: official company website; annual report / "
        "universal registration document; investor presentation; official press "
        "release; reputable business or industry publication; Wikipedia only as "
        "fallback for basic identity.\n"
        "Aim for breadth: cover multiple business lines and recent events rather "
        "than deep-diving one area. Do not cite blogs or weak sources when "
        "official sources exist.\n"
        "CRITICAL: only report facts found in search results. If a search does "
        "not return recent acquisitions, revenue, or leadership changes, do not "
        "guess — write 'Not found in search results' for topics with no results. "
        "Never construct a URL; every Source URL must be copied verbatim from a "
        "search result."
    )


def company_resolution_system_prompt() -> str:
    return (
        "You are a company identity resolution assistant. Given research notes for "
        "an ambiguous company query, resolve the input to the most likely official "
        "company identity.\n"
        "Prefer the official company website and reliable sources. Explicitly "
        "mention ambiguity, including alternative companies or interpretations "
        "when relevant.\n"
        "Only include factual claims supported by the research. Every evidence "
        "item's `source` must be a full URL from the research, not a site name "
        "only."
    )


def company_resolution_user_prompt(company_query: str, research_text: str) -> str:
    return (
        f"Company query: {company_query}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return the resolved company identity. Use `input_name` for the original "
        "query and `resolved_name` for the likely official company name. Include "
        "the official website if available. In `ambiguity_notes`, explain why this "
        "company is the likely match and note credible alternatives. Set "
        "`confidence` from 0.0 to 1.0 based on the evidence strength."
    )


def company_context(profile: CompanyProfileOutput) -> str:
    return (
        f"Company: {profile.company_name}\n\n"
        "Sourced company research text:\n"
        f"{profile.research_text}"
    )


def genai_use_cases_system_prompt() -> str:
    return (
        "You are a senior GenAI opportunity designer. Create 5 narrow, "
        "client-workshop-worthy use cases for one company.\n"
        "First write `ideation_brief` in two parts (cap ~200 words total):\n"
        "Part 1 — OBVIOUS IDEAS TO REJECT: list 3-5 first-order GenAI ideas that "
        "any industry peer could also propose (e.g. predictive maintenance for "
        "equipment, chatbot for customers, document summarization, route "
        "optimization, generic dashboards). Name each and state why it fails the "
        "originality test — the core problem-solution pattern is industry-generic "
        "even if you attach a company product name.\n"
        "Part 2 — UNIQUE MOATS: list 5+ unique company moats from the research — "
        "named assets, recent acquisitions, proprietary platforms, exclusive "
        "partnerships, scale facts, or regulatory positions. For each, note a "
        "non-obvious way GenAI could exploit it — non-obvious means the "
        "problem-solution pairing would surprise a domain expert, not confirm what "
        "they already planned.\n"
        "Then write exactly 5 `use_cases` with consecutive ids uc_1...uc_5. None "
        "may overlap with the rejected obvious ideas.\n\n"
        "COMPANY ANCHORING (most important rule):\n"
        "Each title must contain a company-specific noun — a named product, "
        "platform, acquisition, geography, asset, or initiative from the research. "
        "Titles like 'AI-Powered Compliance' or 'Smart Document Processing' fail "
        "this test. For each use case, write `why_this_company` as: 'This requires "
        "[specific company fact]. Competitors cannot replicate this because "
        "[concrete reason].' If you cannot fill this template, drop the idea.\n"
        "Only use facts that appear verbatim in the research text with a Source "
        "URL. If the research text says 'not found' or lacks a specific detail, "
        "do not invent it. A use case anchored to a well-sourced fact is worth "
        "more than one anchored to a specific but unsourced claim.\n\n"
        "RECENT-NEWS ANCHORING:\n"
        "Prefer use cases tied to events from the last 12 months — acquisitions, "
        "strategic pivots, new markets, regulatory changes, earnings developments. "
        "The research text front-loads recent developments; use them. If the "
        "research did not find recent events, anchor to established facts instead. "
        "Do not fabricate recent developments.\n\n"
        "GENAI MECHANISM DIVERSITY:\n"
        "The 5 candidates must collectively use at least 4 distinct primary "
        "mechanisms from the allowed list. At least one must involve multimodal "
        "input (images, sensor data, video, scanned documents). At least one must "
        "involve agentic tool-use or multi-step orchestration. No two candidates "
        "may share the same primary mechanism AND the same business domain.\n\n"
        "DOMAIN DIVERSITY:\n"
        "Each use case must set `business_domain` to a short snake_case label for "
        "the company division or function it targets. Two use cases that address "
        "the same underlying business process must share the same label, even if "
        "they reference different products, platforms, or sub-segments. Cover at "
        "least 3 distinct `business_domain` values across the 5 candidates. No "
        "more than 2 use cases may share the same `business_domain`.\n\n"
        "QUALITY GATES:\n"
        "Discard ideas where the differentiator is only 'digital transformation', "
        "efficiency, a broad chatbot, generic RAG, a dashboard, or classical "
        "optimization with GenAI branding. GenAI must add value through messy "
        "language, documents, images, conflicting context, retrieval with "
        "reasoning, tool use, structured drafting, or human-reviewable decisions. "
        "Never write that classical systems 'cannot derive', 'cannot handle', or "
        "'are incapable of' something. Instead name what classical systems handle "
        "well (structured optimization, deterministic control, rule-based routing) "
        "and where GenAI adds value on top (interpreting unstructured logs/reports, "
        "explaining anomalies, retrieving procedures, drafting recommendations, "
        "supporting expert review). Also never write 'GenAI is needed' — use "
        "'GenAI adds value by...' instead.\n"
        "Frame GenAI outputs as recommendations, decision briefs, explanations, "
        "or human-approved action plans — not as optimized parameters, optimized "
        "protocols or production optimization\n"
        "WORKFLOW ARCHETYPE EXAMPLES (illustrative, not exhaustive):\n"
        "- Multimodal triage: images/video/sensor data -> structured assessment "
        "with severity and next steps\n"
        "- Regulatory compliance copilot: retrieve regulations, map to company "
        "operations -> gap analysis and action items\n"
        "- Cross-document synthesis: multiple reports/filings -> executive brief "
        "with contradictions flagged\n"
        "- Agentic inspection loop: multi-step tool-use (query DB, call API, "
        "verify) -> verified report\n"
        "- Operator explanation engine: anomaly alert -> root-cause explanation "
        "and SOP retrieval\n"
        "- Proposal/bid drafter: structured data and templates -> client-facing "
        "document draft\n"
        "- Multilingual field intelligence: multilingual field reports -> unified "
        "insights in one language\n"
        "- Training scenario generator: past incidents/cases -> training materials "
        "or simulation scripts\n"
        "Pick from these or define your own, but each of the 5 use cases must "
        "name its workflow archetype and no two may share the same one. "
        "'[Company Product] + optimize/analyze/recommend' is not a distinct "
        "archetype — it is the same data-in-recommendations-out loop with "
        "different nouns.\n\n"
        "ORIGINALITY TEST: strip the company-specific noun from the title and "
        "ask: would this idea appear on a 'top 10 GenAI use cases for [industry]' "
        "listicle? If yes, it is first-order obvious and must be replaced. Good "
        "ideas combine a company-specific asset with a problem or workflow that "
        "competitors are not already pursuing with GenAI. The value of the report "
        "is in surfacing opportunities the client has not yet considered, not "
        "confirming what their digital transformation team already planned. Each "
        "use case must follow a visibly different workflow shape — see the "
        "archetype examples above. You may define your own archetype, but it "
        "must be structurally distinct from the others, not the same "
        "data-in-recommendations-out loop with different nouns.\n"
        "No two use cases may share the same users, problem, and core GenAI "
        "workflow.\n"
        "Use only facts and URLs from the supplied company profile. Do not invent "
        "numeric impact, ROI, pilot results, or targets. `source_backed_metrics` "
        "is empty unless a metric is directly sourced."
    )


def genai_use_cases_user_prompt(company_profile: CompanyProfileOutput) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "Scan the research for quantitative metrics (revenue, headcount, amounts, "
        "market share). When a metric directly supports a use case, populate "
        "`source_backed_metrics` with the exact value and source URL.\n\n"
        "Return `ideation_brief` (list the unique company moats first) and exactly "
        "5 `use_cases` with ids uc_1...uc_5.\n"
        "For each candidate, make `genai_solution` one concrete paragraph covering "
        "inputs/modalities, model+tool loop, generated output, and human approval. "
        "Each pilot KPI must state what to measure, why it matters, measurement "
        "method, baseline, and target direction without numeric targets.\n"
        "Inclusion test: the title names a company-specific noun; `why_this_company` "
        "fills the template 'This requires [fact]. Competitors cannot replicate "
        "because [reason].'; `why_iconic` makes a non-transferability argument; "
        "the workflow shows where GenAI changes expert judgment. "
        "Ground every field in the company research text; URLs only from "
        "that input."
    )


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
        "fact]. A competitor cannot replicate it because [concrete reason].' If you "
        "cannot complete this sentence with a specific fact (not a strategy label "
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
        "Use penalties for peer overlap, vague users or workflows, weak evidence, "
        "generic titles, and `why_iconic` text that only says the idea aligns with "
        "strategy. Compare peer summaries; if the core problem domain (e.g. "
        "regulatory compliance, infrastructure inspection) overlaps with a peer, "
        "cap iconicness at 4 and name the overlapping use_case_id in penalties.\n"
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
    peer_summaries: list[str],
) -> str:
    use_case_json = json.dumps(
        use_case.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    peer_summaries_json = json.dumps(
        peer_summaries,
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company brief:\n"
        f"{grader_company_brief(company_profile)}\n\n"
        "Generated use case to grade (JSON):\n"
        f"{use_case_json}\n\n"
        "Peer use-case summaries for overlap checking only (JSON):\n"
        f"{peer_summaries_json}\n\n"
        "Return exactly one `grade` for the supplied use_case.id. Apply the "
        "report-worthy test before scoring: if the idea would read naturally for a "
        "peer after replacing the company name, say so in weaknesses and penalties, "
        "keep iconicness low, and avoid compensating with high adjacent scores. "
        "Name overlapping peer use_case_ids in penalties. Do not repeat or rewrite "
        "the original use_case object."
    )


def _grader_rubric_brief_lines(score: UseCaseScore) -> list[str]:
    rows = [
        (score.company_relevance, "Company relevance"),
        (score.business_impact, "Business impact"),
        (score.iconicness, "Iconicness"),
        (score.genai_fit, "GenAI fit"),
        (score.feasibility, "Feasibility"),
        (score.evidence_strength, "Evidence strength"),
    ]
    return [f"  - {label}: {line.rationale} — {line.score}/10" for line, label in rows]


def markdown_report_evidence_brief(
    company_profile: CompanyProfileOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    use_case_sections: list[str] = []
    for rank, item in enumerate(final_selection.selected, start=1):
        use_case = item.use_case
        lines = [
            f"### Rank {rank}: {use_case.title}",
            f"- Target users: {', '.join(use_case.target_users)}",
            f"- Fit score for report display: {item.score.weighted_total:.1f}/10",
            f"- Internal weighted score: {item.score.weighted_total}/10",
            f"- Business problem: {use_case.business_problem}",
            f"- Company fit: {use_case.why_this_company}",
            f"- Iconicness (weave into The Opportunity section): {use_case.why_iconic}",
            "- Grader rubric (rationale then score; use in the Scoring subsection):",
            *_grader_rubric_brief_lines(item.score),
            f"- Required data: {use_case.required_data}",
            "- Source-backed metrics:",
        ]
        if use_case.source_backed_metrics:
            lines.extend(
                "- "
                f"{metric.label}: {metric.value} "
                f"[source]({metric.source_url}) - "
                f"{metric.source_quote_or_evidence}"
                for metric in use_case.source_backed_metrics
            )
        else:
            lines.append("- None provided in the source-backed metric fields.")

        lines.append("- Pilot KPIs to validate:")
        for kpi in use_case.pilot_kpis:
            target_direction = kpi.target_direction.replace("_", " ")
            lines.append(
                "- "
                f"{kpi.kpi} matters because {kpi.why_it_matters} "
                f"Measure it with {kpi.measurement_method} "
                f"Compare against {kpi.baseline_needed}; target direction is "
                f"{target_direction}."
            )

        lines.append("- Evidence sources:")
        lines.extend(
            f"- Evidence source [source]({source})"
            for source in use_case.evidence_sources
        )
        lines.append(f"- Company signals: {', '.join(use_case.company_signal_labels)}")

        use_case_sections.append("\n".join(lines))

    use_cases_text = "\n\n".join(use_case_sections)

    return (
        "Citation-ready evidence brief:\n\n"
        f"## Company: {company_profile.company_name}\n\n"
        "## Sourced company research\n"
        f"{company_profile.research_text}\n\n"
        "## Selected use cases\n"
        f"{use_cases_text}"
    )


def markdown_reporter_system_prompt() -> str:
    return (
        "You are writing a client-facing GenAI opportunity report from a completed "
        "use-case discovery workflow. Write like a practical decision memo for "
        "the company's leadership team, not like a generic consulting template. "
        "Return only the requested schema; the `markdown` field must contain the "
        "complete markdown report.\n"
        "Use this template as the report structure and do not leave placeholders:\n"
        "Markdown report template:\n"
        "```markdown\n"
        f"{MARKDOWN_REPORT_TEMPLATE}\n"
        "```\n\n"
        "Use the selected top 3 in order. In the ranked table, format the composite "
        "as a one-decimal Fit score from score.weighted_total with a **/10** suffix "
        "(e.g. 7.4/10, not 7.35/10). The Decision rationale must mention what is "
        "distinctive or, when scores show weak iconicness, why the recommendation "
        "is limited.\n"
        "In `## Company Context`, lead with the most recent and strategically "
        "significant developments from the last 12 months. Do not write a generic "
        "company profile.\n"
        "In each of the three use-case detail sections, include `### Scoring (1–10)`: "
        "a table with columns **Dimension**, **Rationale**, **Score (/10)**. Fill "
        "rationale and score from the JSON `DimensionRubricLine`s; do not invent "
        "them. Weave the iconicness narrative (use_case.why_iconic) into "
        "`### The Opportunity` — do not create a separate Iconicness section. "
        "Do not upgrade a generic use case with new branding language; reflect low "
        "iconicness honestly instead of polishing it into a signature concept. "
        "In `Why GenAI Fits`, use genai_mechanism to explain what GenAI adds "
        "and what classical systems should still handle. Never write that classical "
        "systems 'cannot derive', 'cannot handle', or 'are incapable of' something. "
        "Instead name what classical systems handle well (structured optimization, "
        "deterministic control, rule-based routing) and where GenAI adds value "
        "(interpreting unstructured text, explaining anomalies, retrieving "
        "procedures, drafting recommendations, supporting expert review). "
        "Also never write 'GenAI is needed' — use 'GenAI adds value by...' "
        "instead.\n"
        "In 'How The Workflow Would Work', frame generated outputs as "
        "recommendations for human review — e.g. 'recommended parameter ranges', "
        "'decision brief', 'anomaly explanation', or 'human-approved action plan'. "
        "Never frame them as direct control actions, optimized protocols, "
        "production optimization, or autonomous optimization.\n"
        "Use only supplied facts and URLs. Do not supplement the evidence brief "
        "with general knowledge about the company. If a fact or number is not in "
        "the evidence brief or JSON, it must not appear in the report. Every URL "
        "in the report must appear in the evidence brief — do not construct URLs. "
        "Cite factual claims and numbers with "
        "adjacent neutral markdown links like [source](URL). Do not invent facts, "
        "source URLs, ROI, timelines, pilot results, or numeric targets. "
        "If a source-backed metric's confidence is 'medium' or 'low' in the "
        "evidence brief, note it as approximate or omit it — do not present "
        "it as a verified figure. Write "
        "pilot KPIs as human-readable validation prose. Do not include "
        "`ideation_brief`, `grader_thinking`, raw JSON, or internal pre-analysis.\n"
        "In `## Limitations`, name 2-3 specific data gaps or assumptions — such as "
        "missing internal cost data, unverified regulatory timelines, or revenue "
        "figures from press releases without breakdowns. Do not write "
        "meta-commentary about the report methodology like 'this report relies on "
        "public sources'.\n"
        "In `## Sources`, list each unique URL once as a markdown link with a "
        "descriptive title. Do not classify, tier, or group sources. "
        "Use the descriptive title from the evidence brief for each link. "
        "Do not editorialize or reinterpret what a source covers — if the "
        "URL says 'key figures 30 September', do not relabel it as "
        "'full-year results'."
    )


def markdown_reporter_user_prompt(
    company_profile: CompanyProfileOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    evidence_brief = markdown_report_evidence_brief(
        company_profile,
        final_selection,
    )
    final_selection_json = json.dumps(
        final_selection.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        f"{evidence_brief}\n\n"
        "Selected top 3 use cases with scores (JSON, source of truth for exact "
        "field values like scores, KPIs, and mechanisms):\n"
        f"{final_selection_json}\n\n"
        "Write the final markdown report in the `markdown` field. Use the evidence "
        "brief for citation links and the JSON for exact field values. Do not "
        "include raw JSON, ideation_brief, or grader_thinking."
    )
