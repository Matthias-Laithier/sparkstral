import json
from datetime import date

from src.schemas import (
    CompanyProfileOutput,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    PainPointProfilerOutput,
)


def web_search_system_prompt(today: date) -> str:
    return (
        "You are a research assistant. Use web search to find accurate, "
        "up-to-date information. Cite the source URL for every fact you report. "
        "Be concise and to the point. "
        f"The current date is {today:%Y-%m-%d}; use it in searches when recency "
        "matters."
    )


def company_research_prompt(company_query: str) -> str:
    return (
        f"Research this company: {company_query}\n\n"
        "Gather: official or common company name; primary industry; 2-5 business "
        "lines; key customers or segments if public; 2-5 strategic priorities; "
        "include the source URL next to each fact.\n"
        "Use few sources: prefer Wikipedia, plus at most one or two other reliable "
        "pages."
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
        "extract and return a structured profile.\n"
        "Only include information supported by the research.\n"
        "For every evidence item, `source` must be a full URL (https preferred), "
        "from the research - not a site name only."
    )


def company_profile_user_prompt(company_query: str, research_text: str) -> str:
    return (
        f"Company query: {company_query}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return the structured profile with only the most relevant information. "
        "Be concise: 2-5 items each for business_lines, key_customers, and "
        "strategic_priorities."
    )


def company_context(profile: CompanyProfileOutput) -> str:
    return "Known company profile (from prior step):\n" + json.dumps(
        profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )


def pain_point_research_prompt(profile: CompanyProfileOutput) -> str:
    return (
        "Search the web for major pain points, unmet needs, and structural "
        "challenges in the company's field.\n\n"
        f"{company_context(profile)}\n\n"
        "Use few sources: prefer Wikipedia, plus at most one or two other reliable "
        "pages.\n"
        "Include the full URL for each finding you cite."
    )


def pain_point_system_prompt() -> str:
    return (
        "You are an analyst. Given research notes, extract major pain points, "
        "industry gaps, or unmet needs relevant to the company and its field.\n"
        "Only include points supported by the research. Assign prominence 1-10 "
        "from the evidence strength and business impact. Each pain point's "
        "sources must be full URL strings from the research."
    )


def pain_point_user_prompt(
    profile: CompanyProfileOutput,
    research_text: str,
) -> str:
    return (
        f"{company_context(profile)}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return 3-8 pain points. Be specific and avoid duplication."
    )


def genai_use_cases_system_prompt() -> str:
    return (
        "You are a principal GenAI strategy consultant. You receive a structured "
        "company profile and structured pain-point analysis. Produce a candidate "
        "pool of 8-12 company-specific generative-AI use cases that feel iconic "
        "for THIS company, not interchangeable with any other business.\n"
        "This is one ideation call. Do not create separate outputs or agents per "
        "lens. Use these ideation lenses across the pool: grounded consultant, "
        "moonshot strategist, operations expert, customer/partner expert, and "
        "risk/compliance expert. Every candidate must include its ideation_lens.\n"
        "Generate use cases directly from the company profile, pain points, "
        "strategic priorities, business lines, and evidence URLs. Be concrete: "
        "name workflows, data, org roles, and what makes the solution "
        "distinctive. Link every candidate to at least one pain point title from "
        "the input.\n"
        "Every use case must be explicitly GenAI-native. The core value must "
        "come from language/document reasoning, generation, tool orchestration, "
        "decision support, multimodal understanding, or workflow synthesis. "
        "For each candidate, genai_mechanism must explain why GenAI is needed, "
        "why ordinary software is not enough, and why classical ML or "
        "optimization is not enough.\n"
        "Reject or reframe ideas that are mainly predictive maintenance, "
        "numerical forecasting, process optimization, control systems, "
        "dashboards, generic RAG, or a generic chatbot. These can only be "
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
        "from company profile evidence or pain-point sources.\n"
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
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Output 8-12 candidate use cases. Each must have: id; title; "
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
        "approval step exists. Use the company profile, business lines, "
        "strategic priorities, pain points, and evidence URLs directly. "
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
        "- evidence_strength: how strongly the candidate is supported by supplied "
        "company facts, pain points, and source URLs.\n"
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
        "and penalties for each use case. Do not output weighted_total because "
        "code computes it. Do not choose final recommendations."
    )


def markdown_reporter_system_prompt() -> str:
    return (
        "You are a senior GenAI strategy consultant writing the client-ready "
        "markdown deliverable from a completed use-case discovery workflow.\n"
        "Return only structured data matching the requested schema. The `markdown` "
        "field must contain the complete markdown report.\n"
        "Write polished, professional prose for executives and business owners. "
        "Make the report feel like a finished consulting deliverable, not a raw "
        "data dump. Use clear markdown structure with: title, executive summary, "
        "company context, selection methodology, ranked recommendations table, "
        "detailed sections for each of the 3 use cases, caveats, and sources.\n"
        "Use the final selected top 3 use cases directly. Preserve their order as "
        "rank 1, rank 2, and rank 3. Include weighted scores and important score "
        "breakdowns in the ranked table or use-case sections. Make each use case "
        "easy to scan with business problem, proposed GenAI solution, why it fits "
        "the company, a section titled `Expected Impact and KPIs`, required data, "
        "feasibility, risks, and supporting sources. In `Expected Impact and "
        "KPIs`, render source-backed metrics separately from pilot KPIs. If "
        "source_backed_metrics is empty, do not write any metric as a factual "
        "expected result; use the qualitative impact and pilot KPIs as the "
        "validation plan. For each use case, include a short section titled "
        "`Why this is GenAI` that uses the use case's genai_mechanism values: "
        "the mechanisms, why GenAI is needed, why classical software is not "
        "enough, and why classical ML or optimization is not enough.\n"
        "Explain the selection methodology using only the supplied artifacts: "
        "company research, pain-point profiling, use-case generation, scoring, "
        "and final top-3 selection.\n"
        "Use only facts, caveats, scores, and source URLs from the supplied JSON. "
        "Do not invent new facts, metrics, timelines or source URLs. Keep source "
        "URLs as full URLs copied from the input. Do not write these phrases "
        "unless the claim is directly supported by source_backed_metrics: "
        "'pilot results show', 'lab data shows', 'expected 30%', "
        "'will reduce by', or 'will improve by'."
    )


def markdown_reporter_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    final_selection: FinalSelectionOutput,
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
    final_selection_json = json.dumps(
        final_selection.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Selected top 3 use cases with scores (JSON):\n"
        f"{final_selection_json}\n\n"
        "Write the final client-ready markdown report in the `markdown` field. "
        "Use these JSON inputs as the source of truth. Start with a concise H1 "
        "title for the company, then include an executive summary, company "
        "context, selection methodology, a ranked recommendations table, detailed "
        "sections for each of the 3 selected use cases, caveats, and sources. "
        "For each use case, include the business problem, proposed GenAI solution, "
        "why it fits the company, `Expected Impact and KPIs`, required data, "
        "score, feasibility, risks, a short `Why this is GenAI` section based "
        "on genai_mechanism, and supporting source URLs. In `Expected Impact "
        "and KPIs`, show source_backed_metrics separately from pilot_kpis; "
        "pilot KPIs describe what to validate and must not be written as proven "
        "results. "
        "Use professional markdown formatting with headings, bullets, and tables "
        "where useful, but do not include raw JSON or unsupported claims."
    )
