import json
from datetime import date
from pathlib import Path

from src.schemas import (
    CompanyProfileOutput,
    CompanyResolutionOutput,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    GenAIUseCaseIdPrefix,
    GenAIUseCasePersona,
    PainPointProfilerOutput,
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
        "matters."
    )


def company_research_prompt(company_resolution: CompanyResolutionOutput) -> str:
    resolution_json = json.dumps(
        company_resolution.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Research this resolved company comprehensively: "
        f"{company_resolution.resolved_name}\n\n"
        "Structured company resolution from the previous step (JSON):\n"
        f"{resolution_json}\n\n"
        "Use the structured company resolution as the known starting point. Treat "
        "official name/resolved_name, website, headquarters_country, "
        "primary_industry, "
        "ambiguity_notes, confidence, and evidence URLs as already acquired "
        "identity context. Do not spend the research repeating basic identity "
        "discovery unless the resolution evidence is weak or ambiguous.\n"
        "Preserve and reuse useful URLs from company_resolution.evidence and the "
        "official website when they support later profile claims. Search for the "
        "missing context needed for a client-style GenAI recommendation workflow: "
        "business lines; key customers; customer segments; strategic priorities; "
        "recent strategic initiatives; geography/markets; operational pain "
        "points; regulatory pressure; customer/market pressure; strategic growth "
        "opportunities; and technology/digital transformation context. Put the "
        "source URL next to every factual claim.\n"
        "Format every research bullet exactly with: Claim: one concise factual "
        "claim; Source URL: one full http(s) URL; Citation: a short quote, page "
        "title, section name, or faithful source detail supporting the claim. "
        "Omit claims that do not have a full source URL. Do not summarize uncited "
        "facts. Do not cite source names without URLs.\n"
        "Prefer sources in this order: official company website; annual report / "
        "universal registration document; investor presentation; official "
        "strategy page; official press release; regulator / government / "
        "standards body; reputable business or industry publication; Wikipedia "
        "only as fallback for basic identity, never as core evidence for "
        "recommendations.\n"
        "Keep searches reasonable: use several high-quality sources that cover the "
        "company and its market, not broad low-value browsing. Prefer many "
        "claim-level findings with citations over a shallow summary. Do not cite "
        "Wikipedia, blogs, or weak sources as primary evidence if official or "
        "reputable sources exist. Do not invent facts when sources are missing. "
        "Clearly mark uncertainty, including uncertainty from ambiguity_notes or "
        "low resolution confidence."
    )


def company_resolution_research_prompt(company_query: str) -> str:
    return (
        f"Resolve this company name to the most likely official company: "
        f"{company_query}\n\n"
        "Find the likely official company identity before deeper research. Prefer "
        "the official company website, then reliable sources such as company "
        "registries, annual reports, reputable news, Wikipedia, or Crunchbase. "
        "Explicitly look for ambiguity: similarly named companies, subsidiaries, "
        "brands, regional variants, or common meanings of the name.\n"
        "Gather: official/resolved name; official website; headquarters country; "
        "primary industry; ambiguity notes; and source URLs next to each factual "
        "claim.\n"
        "Use few sources: prefer Wikipedia, plus at most one or two other reliable "
        "pages."
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


def company_profile_system_prompt() -> str:
    return (
        "You are a data extraction assistant. Given research notes about a company, "
        "extract and return a compact profile plus a strict cited claim ledger "
        "that subsequent strategy steps can use as their evidence base.\n"
        "Only include information supported by the research. Capture company "
        "profile facts, market context, pain-point signals, regulatory context, "
        "growth opportunities, and technology transformation context when "
        "supported.\n"
        "The `claims` field is the primary evidence ledger. Every claim must have "
        "a full source_url copied exactly from the research - not a site name only. "
        "Drop uncited claims. Never merge multiple unrelated facts into one claim. "
        "Use compact profile fields as summaries derived from `claims`, not as "
        "replacements for them."
    )


def company_profile_user_prompt(company_query: str, research_text: str) -> str:
    return (
        f"Company query: {company_query}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return the structured profile with only sourced, relevant information. "
        "Fill every field from the research: company_name; industry; "
        "business_lines; key_customers; customer_segments; strategic_priorities; "
        "recent_strategic_initiatives; geography_markets; operational_context; "
        "regulatory_context; customer_market_pressure; growth_opportunities; "
        "technology_transformation_context; claims. Be concise: 2-6 "
        "items for compact list fields where the research supports them. Include "
        "at least 15 claims. Each claims item must contain one factual claim, "
        "source_url, and citation. Copy source_url exactly from the research text. "
        "Drop facts without full URLs or citations. Do not invent missing facts."
    )


def company_context(profile: CompanyProfileOutput) -> str:
    return "Known company profile (from prior step):\n" + json.dumps(
        profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )


def pain_point_system_prompt() -> str:
    return (
        "You are an analyst. Given an enriched structured company profile, extract "
        "major pain points, industry gaps, unmet needs, and opportunity pressures "
        "relevant to the company and its field.\n"
        "Only include points supported by company_profile.claims and their evidence "
        "URLs. Assign prominence 1-10 from the evidence strength and business "
        "impact. Each pain point's sources must be full URL strings already "
        "present in company_profile.claims.source_url. Do not add new web "
        "research, invent unsupported industry generalizations, or cite URLs not "
        "present in the profile."
    )


def pain_point_user_prompt(
    profile: CompanyProfileOutput,
) -> str:
    return (
        f"{company_context(profile)}\n\n"
        "Return 3-8 pain points derived only from this enriched company profile. "
        "Use the operational_context, regulatory_context, "
        "customer_market_pressure, growth_opportunities, "
        "technology_transformation_context, strategic_priorities, and claims "
        "fields directly. Be specific, avoid duplication, and copy each source URL "
        "from company_profile.claims."
    )


PERSONA_GUIDANCE: dict[GenAIUseCasePersona, str] = {
    "grounded consultant": (
        "Stay practical, evidence-led, and implementation-aware. Prefer use cases "
        "that a serious client team could pilot with known workflows, data, and "
        "approval paths."
    ),
    "moonshot strategist": (
        "Think ambitiously and optimistically about strategic advantage. Propose "
        "ideas that are bold and memorable while still grounded in the supplied "
        "company facts, pain points, and GenAI-native mechanisms."
    ),
    "why not? inventor": (
        "Look for unusual, surprising, and novel ideas. Push beyond default "
        "consulting recommendations, but keep every idea tied to the company's "
        "real context and make feasibility tradeoffs explicit."
    ),
}


def genai_use_cases_system_prompt(
    ideation_lens: GenAIUseCasePersona,
    id_prefix: GenAIUseCaseIdPrefix,
) -> str:
    expected_ids = ", ".join(f"{id_prefix}_{index}" for index in range(1, 4))
    return (
        f"You are the {ideation_lens} GenAI use-case generator. "
        f"{PERSONA_GUIDANCE[ideation_lens]}\n"
        "You receive a structured company profile and structured pain-point "
        "analysis. Produce exactly 3 company-specific generative-AI use cases "
        "that feel iconic "
        "for THIS company, not interchangeable with any other business.\n"
        f"Every candidate must set ideation_lens exactly to `{ideation_lens}`. "
        f"Use exactly these IDs, one per candidate: {expected_ids}. Do not use "
        "any other ID format.\n"
        "Generate use cases directly from the company profile, "
        "company_profile.claims, pain points, strategic priorities, business "
        "lines, and evidence URLs. Be concrete: name workflows, data, org roles, "
        "and what makes the solution distinctive. Link every candidate to at "
        "least one pain point title from the input.\n"
        "Every use case must be explicitly GenAI-native. The core value must "
        "come from language/document reasoning, generation, tool orchestration, "
        "decision support, multimodal understanding, or workflow synthesis. "
        "For each candidate, genai_mechanism must explain why GenAI is needed, "
        "why ordinary software is not enough, and why classical ML or "
        "optimization is not enough.\n"
        "Reject or reframe ideas that could be done without GenAI. These can only be "
        "accepted if the core value comes from a specific GenAI mechanism tied "
        "to the company's language, documents, decisions, multimodal inputs, "
        "tools, or workflows; otherwise replace them with a stronger "
        "GenAI-native idea.\n"
        "STRICT: Do not propose overused, generic product ideas, including: "
        "generic customer support chatbot, internal knowledge assistant or RAG "
        "for documents, or generic marketing copy generators, unless the write-up "
        "is so specific to this company that it is clearly not a default listing.\n"
        "Do not discuss vendor, model-provider, or "
        "platform fit. "
        "Preserve evidence: evidence_sources must be full URL strings copied "
        "from company_profile.claims.source_url or pain-point sources.\n"
        "Do not invent numeric impact, expected percentage improvements, ROI, "
        "pilot results, lab results, or deployment outcomes. Only put numbers "
        "in source_backed_metrics when the metric value is directly supported "
        "by a full URL already present in evidence_sources. If no sourced "
        "metric exists, use an empty source_backed_metrics list, describe "
        "impact qualitatively, and provide pilot_kpis that say what should be "
        "measured. Pilot KPIs must not include invented numeric targets such "
        "as '30% reduction'."
    )


def genai_use_cases_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    ideation_lens: GenAIUseCasePersona,
    id_prefix: GenAIUseCaseIdPrefix,
) -> str:
    expected_ids = ", ".join(f"{id_prefix}_{index}" for index in range(1, 4))
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    pain_json = json.dumps(
        pain_points.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        f"Output exactly 3 candidate use cases as the {ideation_lens}. Use "
        f"exactly these IDs: {expected_ids}. Each candidate's ideation_lens "
        f"must be exactly `{ideation_lens}`. Each must have: id; title; "
        "target_users (1+); business_problem; why_this_company; genai_solution; "
        "genai_mechanism with mechanisms (1+) and the three why_* fields; "
        "required_data; qualitative_impact; source_backed_metrics; pilot_kpis "
        "(2+); why_iconic; feasibility_notes; risks (1+); linked_pain_points "
        "(1+ exact or clearly recognizable pain-point titles from the input); "
        "evidence_sources (1+ full URLs copied from prior inputs); and "
        "ideation_lens. source_backed_metrics may be empty if no real metric "
        "exists, but every included metric's source_url must be copied from "
        "evidence_sources. Each pilot_kpi must describe what to measure, why it "
        "matters, how to measure it, the target direction, and the baseline "
        "needed; do not invent target values or write claims like 'expected "
        "30%'. Each genai_solution must describe a concrete user workflow: who "
        "uses it, what they input, what the system generates, and what human "
        "approval step exists. Use company_profile.claims, the company profile, "
        "business lines, strategic priorities, pain points, and evidence URLs "
        "directly. "
    )


def use_case_deduplicator_system_prompt() -> str:
    return (
        "You are a GenAI use-case deduplication agent. Your sole purpose is to "
        "find clusters of very similar use cases and keep the strongest existing "
        "representative from each cluster.\n"
        "Return only existing use_case IDs in retained_use_case_ids. Do not "
        "rewrite, refine, merge fields, rename, reorder, create new IDs, or "
        "change any use case content. Application code will preserve the original "
        "use case objects exactly as provided.\n"
        "Only remove near-duplicates: use cases that solve substantially the same "
        "business problem for substantially the same users with substantially the "
        "same GenAI workflow. Do not remove distinct ideas merely because they "
        "share a pain point, data source, user group, or broad theme.\n"
        "When a duplicate cluster exists, keep the strongest existing use case: "
        "the candidate with better company specificity, evidence, concrete "
        "workflow, GenAI fit, feasibility, and iconicness. Retain at least 5 "
        "use cases. If removing duplicates would leave fewer than 5, retain the "
        "5 strongest existing use cases."
    )


def use_case_deduplicator_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    use_cases: list[GenAIUseCaseCandidate],
) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    pain_json = json.dumps(
        pain_points.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    use_cases_json = json.dumps(
        [use_case.model_dump(mode="json") for use_case in use_cases],
        indent=2,
        ensure_ascii=False,
    )
    use_case_ids = ", ".join(use_case.id for use_case in use_cases)
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Generated use cases to deduplicate (JSON):\n"
        f"{use_cases_json}\n\n"
        f"Available use_case IDs: {use_case_ids}.\n"
        "Return retained_use_case_ids only. Every retained ID must be copied "
        "exactly from the available IDs above. Retain at least 5 use cases. "
        "Do not output rewritten use cases, merged use cases, explanations, "
        "clusters, replacement IDs, or changed fields."
    )


def use_case_grader_system_prompt() -> str:
    return (
        "You are a strict GenAI use-case grading analyst. Given a company profile, "
        "pain-point analysis, and genai use-case candidate pool, grade every provided "
        "use case with an explicit rubric. Do not skip, merge, rewrite, refine, "
        "red-team, or anything else.\n"
        "Be harsh and discriminate between strong company-specific ideas and generic "
        "ones. Scores of 5 should be rare and reserved for use cases with unusually "
        "strong evidence, company specificity, GenAI fit, and business value. Most "
        "ordinary acceptable ideas should receive 2-4, not 4-5.\n"
        "Score each rubric dimension from 1 (weak) to 5 (excellent):\n"
        "- company_relevance: how specifically the use case fits this company's "
        "business lines, priorities, users, and context.\n"
        "- business_impact: expected operational, financial, customer, risk, or "
        "strategic value if executed well.\n"
        "- iconicness: whether this feels distinctive and memorable for this "
        "company, not a default GenAI idea.\n"
        "- genai_fit: whether generative AI is genuinely needed for language, "
        "reasoning, synthesis, generation, or multimodal work beyond ordinary "
        "software or analytics.\n"
        "- feasibility: whether required data, workflows, integration paths, "
        "change management, and risks look practical.\n"
        "- evidence_strength: how strongly the candidate is supported by "
        "company_profile.claims, pain points, and source URLs.\n"
        "Penalize generic candidates harshly. Generic chatbot, RAG, internal "
        "knowledge assistant, document search, marketing generator, or broad "
        "productivity automation ideas should score low unless they are deeply and "
        "unmistakably grounded in the company's specific operations, users, data, "
        "workflow, and evidence.\n"
        "Use cases that are mostly classical ML, forecasting, optimization, rules, "
        "dashboards, or workflow automation should receive low genai_fit, even if "
        "they may be useful. Unsupported metrics and invented impact claims should "
        "lower evidence_strength. Weak, vague, or only tangential source quality "
        "should also lower evidence_strength. Vague target users, missing workflow "
        "steps, unclear data access, or unclear human approval should lower "
        "feasibility.\n"
        "For every material weakness, include a short penalties entry. Penalize weak "
        "company specificity, vague impact, unclear need for GenAI, missing evidence, "
        "unsupported claims, unrealistic implementation, and risks that make the "
        "idea hard to deploy.\n"
        "Do not add any criterion beyond the stated ones. "
        "The rubric is only: company_relevance, business_impact, "
        "iconicness, genai_fit, feasibility, and evidence_strength.\n"
        "For each grade, include use_case_id, strengths, weaknesses, rationale, "
        "penalties, and the six rubric fields. Do not repeat or rewrite the "
        "original use_case objects. Do not output weighted_total; application "
        "code will compute it from the six rubric fields."
    )


def use_case_grader_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    use_cases: list[GenAIUseCaseCandidate],
) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    pain_json = json.dumps(
        pain_points.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    use_cases_json = json.dumps(
        [use_case.model_dump(mode="json") for use_case in use_cases],
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Generated use cases to grade (JSON):\n"
        f"{use_cases_json}\n\n"
        "Return one grades item for every use case above. Each item must use "
        "use_case_id equal to the matching use_case.id. Do not repeat, copy, "
        "or rewrite any original use_case object. Grade strictly using only "
        "the six rubric fields: "
        "company_relevance, business_impact, iconicness, genai_fit, feasibility, "
        "and evidence_strength. Include strengths, weaknesses, rationale, "
        "and penalties for each use case."
    )


def _source_links(sources: list[str]) -> str:
    return " ".join(f"[source]({source})" for source in sources)


def markdown_report_evidence_brief(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    claim_lines_by_source: dict[str, list[str]] = {}
    company_claim_lines: list[str] = []
    for claim in company_profile.claims:
        line = f"- {claim.claim} [source]({claim.source_url}) - {claim.citation}"
        company_claim_lines.append(line)
        claim_lines_by_source.setdefault(claim.source_url, []).append(line)

    pain_point_lines = [
        "- "
        f"{pain_point.title}: {pain_point.description} "
        f"(prominence {pain_point.prominence}/10) "
        f"{_source_links(pain_point.sources)}"
        for pain_point in pain_points.pain_points
    ]

    use_case_sections: list[str] = []
    for rank, item in enumerate(final_selection.selected, start=1):
        use_case = item.use_case
        lines = [
            f"### Rank {rank}: {use_case.title}",
            f"- Target users: {', '.join(use_case.target_users)}",
            f"- Weighted score: {item.score.weighted_total}",
            f"- Business problem: {use_case.business_problem}",
            f"- Company fit: {use_case.why_this_company}",
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
        lines.extend(
            "- "
            f"{kpi.kpi}: measure via {kpi.measurement_method}; "
            f"baseline needed: {kpi.baseline_needed}; "
            f"target direction: {kpi.target_direction}"
            for kpi in use_case.pilot_kpis
        )

        lines.append("- Evidence matched to company claims:")
        matched_evidence = [
            line
            for source in use_case.evidence_sources
            for line in claim_lines_by_source.get(source, [])
        ]
        if matched_evidence:
            lines.extend(matched_evidence)
        else:
            lines.extend(
                f"- Evidence source [source]({source})"
                for source in use_case.evidence_sources
            )

        use_case_sections.append("\n".join(lines))

    company_claims_text = "\n".join(company_claim_lines)
    pain_points_text = "\n".join(pain_point_lines)
    use_cases_text = "\n\n".join(use_case_sections)

    return (
        "Citation-ready evidence brief:\n\n"
        "## Company claims\n"
        f"{company_claims_text}\n\n"
        "## Pain points\n"
        f"{pain_points_text}\n\n"
        "## Selected use cases\n"
        f"{use_cases_text}"
    )


def markdown_reporter_system_prompt() -> str:
    return (
        "You are writing a client-facing GenAI opportunity report from a completed "
        "use-case discovery workflow. Write like a practical decision memo for "
        "the company's leadership team, not like a generic consulting template.\n"
        "Return only structured data matching the requested schema. The `markdown` "
        "field must contain the complete markdown report.\n"
        "Use the markdown template below as a writing blueprint. Keep the major "
        "section order and ranked opportunities table, but write natural, dense "
        "prose inside each section. Do not leave placeholder text or blank form "
        "rows in the final markdown.\n\n"
        "Markdown report template:\n"
        "```markdown\n"
        f"{MARKDOWN_REPORT_TEMPLATE}\n"
        "```\n\n"
        "Use the final selected top 3 use cases directly. Preserve their order as "
        "rank 1, rank 2, and rank 3. Put score.weighted_total in the ranked "
        "opportunities table as the weighted score. Briefly explain the scoring "
        "rubric using only these dimensions: company relevance, business impact, "
        "iconicness, GenAI fit, feasibility, and evidence strength.\n"
        "For each use case, write `How The Workflow Would Work` with four "
        "numbered steps: user input; retrieved or generated context; generated "
        "output; and human approval or decision point. Make the workflow specific "
        "enough that a pilot team could understand what would be built.\n"
        "In `Why GenAI Is Needed`, use the use case's genai_mechanism values: the "
        "mechanisms, why GenAI is needed, why classical software is not enough, "
        "and why classical ML or optimization is not enough.\n"
        "In `Impact To Validate`, separate source-backed metrics from pilot "
        "KPIs. Source-backed metrics may be stated as factual only when present "
        "in source_backed_metrics and must include an adjacent markdown link to "
        "source_backed_metrics.source_url. Pilot KPIs are validation measures; "
        "do not write them as proven results and do not add fake numeric targets.\n"
        "Every factual claim and every number in the markdown report must have an "
        "adjacent embedded markdown link to the source URL supporting that claim, "
        "using only URLs from company_profile.claims, pain-point sources, "
        "source_backed_metrics.source_url, or evidence_sources. The only numbers "
        "that do not need external source links are ranks and scores copied from "
        "the final_selection JSON.\n"
        "Use the citation-ready evidence brief before the raw JSON when choosing "
        "which claims to write. Each paragraph should contain concrete company "
        "facts, workflow artifacts, users, data, metrics, risks, or caveats from "
        "the supplied inputs. Avoid filler sentences that would apply to any "
        "company. Do not repeat the same company context sentence across all "
        "three use cases; each use case should add new detail.\n"
        "Use only facts, caveats, scores, company_profile.claims, pain points, "
        "selected use cases, and source URLs from the supplied JSON. Do not invent "
        "new facts, metrics, timelines, ROI, pilot designs, deployment status, or "
        "source URLs. If evidence is weak, public-source-only, or missing internal "
        "data, say so in the relevant section and in Caveats.\n"
        "No generic hype. No fake pilots. No fake numeric improvements. Do not "
        "write broad claims such as 'GenAI will transform everything'. Prefer "
        "concrete workflows over abstract strategy. Do not write these phrases "
        "unless the claim is directly supported by source_backed_metrics: "
        "'pilot results show', 'lab data shows', 'expected 30%', "
        "'will reduce by', or 'will improve by'."
    )


def markdown_reporter_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    evidence_brief = markdown_report_evidence_brief(
        company_profile,
        pain_points,
        final_selection,
    )
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    pain_json = json.dumps(
        pain_points.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    final_selection_json = json.dumps(
        final_selection.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        f"{evidence_brief}\n\n"
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Selected top 3 use cases with scores (JSON):\n"
        f"{final_selection_json}\n\n"
        "Write the final markdown report in the `markdown` field. Use these JSON "
        "inputs as the source of truth, and use the citation-ready evidence brief "
        "above as the easiest source for inline markdown links. Follow the "
        "system prompt's report structure, citation rules, density rules, KPI "
        "rules, and no-hallucination rules. Do not include raw JSON."
    )
