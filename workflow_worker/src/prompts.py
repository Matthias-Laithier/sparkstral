import json
from datetime import date

from src.schemas import (
    CompanyProfileOutput,
    FinalReport,
    FinalSelectionOutput,
    GenAIUseCaseCandidate,
    GenAIUseCaseCandidatePool,
    GradedUseCase,
    OpportunityMapOutput,
    PainPointProfilerOutput,
    RedTeamOutput,
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


def opportunity_mapper_system_prompt() -> str:
    return (
        "You are a GenAI opportunity mapping strategist. Given a structured "
        "company profile and structured pain-point analysis, map the company's "
        "facts and pain points into 3-8 GenAI-shaped opportunity areas.\n"
        "Do not produce final use cases yet. Stay one level higher than a "
        "solution design: identify opportunity territories that could later "
        "become use cases.\n"
        "Avoid generic opportunities such as 'improve efficiency', 'automate "
        "support', or 'increase productivity' unless they are made specific to "
        "the company's business lines, pain points, data, and operating context.\n"
        "For every opportunity, explain why it matters, why GenAI is suitable "
        "rather than ordinary software or analytics, and which likely data "
        "sources would be needed. Link each opportunity to at least one named "
        "pain point from the input.\n"
        "Evidence sources must be full URL strings taken only from the prior "
        "company profile evidence or pain-point sources."
    )


def opportunity_mapper_user_prompt(
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
        "Return an opportunity map with 3-8 opportunities and a concise summary. "
        "Each opportunity must include: title; business_line; linked_pain_points "
        "(1+ exact or clearly recognizable pain-point titles from the input); "
        "why_it_matters; why_genai_is_suitable; likely_data_sources (1+); and "
        "evidence_sources (1+ full URLs copied from the profile evidence or pain "
        "point sources). Do not write final use cases or implementation plans."
    )


def genai_use_cases_system_prompt() -> str:
    return (
        "You are a principal GenAI strategy consultant. You receive a structured "
        "company profile, structured pain-point analysis, and opportunity map. "
        "Produce a candidate pool of 8-12 company-specific generative-AI use "
        "cases that feel iconic for THIS company, not interchangeable with any "
        "other business.\n"
        "This is one ideation call. Do not create separate outputs or agents per "
        "lens. Use these ideation lenses across the pool: grounded consultant, "
        "moonshot strategist, operations expert, customer/partner expert, and "
        "risk/compliance expert. Every candidate must include its ideation_lens.\n"
        "Each candidate must tie to the company profile, pain points, opportunity "
        "map, industry, and strategic priorities. Be concrete: name workflows, "
        "data, org roles, and what makes the solution distinctive. Link every "
        "candidate to at least one opportunity title from the input.\n"
        "STRICT: Do not propose overused, generic product ideas, including: "
        "generic customer support chatbot, internal knowledge assistant or RAG "
        "for documents, or generic marketing copy generators, unless the write-up "
        "is so specific to this company that it is clearly not a default listing.\n"
        "Do not discuss vendor, model-provider, or "
        "platform fit. "
        "Preserve evidence: evidence_sources must be full URL strings copied "
        "from prior company profile evidence, pain-point sources, or opportunity "
        "evidence_sources."
    )


def genai_use_cases_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    opportunity_map: OpportunityMapOutput,
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
    opportunity_json = json.dumps(
        opportunity_map.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Opportunity map (JSON):\n"
        f"{opportunity_json}\n\n"
        "Output 8-12 candidate use cases. Each must have: id; title; "
        "target_users (1+); business_problem; why_this_company; genai_solution; "
        "required_data; expected_impact; why_iconic; feasibility_notes; risks "
        "(1+); linked_opportunities (1+ opportunity titles from the input); "
        "evidence_sources (1+ full URLs copied from prior inputs); and "
        "ideation_lens. Use the opportunity map as the bridge from pain points "
        "to candidates. Do not rank, score, or choose a final top 3."
    )


def deduper_system_prompt() -> str:
    return (
        "You are a GenAI use-case deduplication editor. Given an 8-12 item "
        "candidate pool generated from several ideation lenses, return a merged "
        "pool of 6-10 candidates.\n"
        "Remove near duplicates and merge overlapping candidates when they solve "
        "the same business problem for the same users or workflow. When merging, "
        "keep the strongest company-specific details from each candidate.\n"
        "Prefer the more company-specific candidate over a generic one. Preserve "
        "diversity across ideation_lens values where possible, while keeping the "
        "best candidates.\n"
        "Preserve evidence: every evidence_sources URL from merged candidates "
        "that still supports the retained use case must be copied into the "
        "retained candidate's evidence_sources. Do not invent new URLs.\n"
        "Explain removed or merged candidates in removed_or_merged. The rationale "
        "should summarize the deduplication logic. Do not grade, score, rank, or "
        "write a final report."
    )


def deduper_user_prompt(candidates: GenAIUseCaseCandidatePool) -> str:
    candidates_json = json.dumps(
        candidates.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Candidate use-case pool (JSON):\n"
        f"{candidates_json}\n\n"
        "Return a deduplicated pool with 6-10 use cases. Remove near duplicates; "
        "merge overlapping candidates by preserving the strongest details, "
        "including title specificity, target users, business problem, company fit, "
        "solution details, required data, expected impact, feasibility notes, "
        "risks, linked opportunities, evidence source URLs, and ideation lens "
        "diversity. Keep the more company-specific candidate when deciding what "
        "survives. In removed_or_merged, list which candidate ids or titles were "
        "removed or merged and why."
    )


def use_case_grader_system_prompt() -> str:
    return (
        "You are a strict GenAI use-case grading analyst. Given a company profile, "
        "pain-point analysis, opportunity map, and genai use-case idea pool, "
        "grade every provided use case with an explicit rubric. Do not skip, merge, "
        "rewrite, refine, red-team, or anything else.\n"
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
        "company facts, pain points, opportunities, and source URLs.\n"
        "Penalize generic candidates harshly. A generic chatbot, document search "
        "assistant, marketing generator, or broad productivity automation should "
        "score low unless the candidate is unmistakably grounded in the company's "
        "specific operations, users, data, and evidence.\n"
        "Penalize weak company specificity, vague impact, unclear need for GenAI, "
        "missing evidence, unsupported claims, unrealistic implementation, and "
        "risks that make the idea hard to deploy.\n"
        "Do not add any criterion beyond the stated ones. "
        "The rubric is only: company_relevance, business_impact, "
        "iconicness, genai_fit, feasibility, and evidence_strength.\n"
        "For each score, include rationale, strengths, and weaknesses. Set total "
        "to the sum of the six rubric fields."
    )


def use_case_grader_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    opportunity_map: OpportunityMapOutput,
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
    opportunity_json = json.dumps(
        opportunity_map.model_dump(mode="json"),
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
        "Opportunity map (JSON):\n"
        f"{opportunity_json}\n\n"
        "Deduplicated use cases to grade (JSON):\n"
        f"{use_cases_json}\n\n"
        "Return one graded_use_cases item for every use case above. Keep each "
        "original use_case object unchanged. For score.use_case_id, use the "
        "matching use_case.id. Grade strictly using only the six rubric fields: "
        "company_relevance, business_impact, iconicness, genai_fit, feasibility, "
        "and evidence_strength. Include total, rationale, strengths, and "
        "weaknesses for each use case. Do not choose final recommendations."
    )


def red_team_system_prompt() -> str:
    return (
        "You are a strict red-team critic for GenAI use-case strategy. Given the "
        "company context and the initial top 5 graded use cases, identify "
        "weaknesses and required fixes before any refinement happens.\n"
        "Do not rewrite, rename, merge, rank, refine, or improve the use cases. "
        "Only critique them.\n"
        "For each selected use case, return exactly one review with at least one "
        "structured criticism. Every review's use_case_id must match one selected "
        "use_case.id.\n"
        "Criticize generic ideas harshly. Flag unsupported claims, weak or "
        "unclear evidence, weak feasibility, vague implementation assumptions, "
        "unclear business impact, unclear target users, and ideas that do not "
        "really need GenAI beyond ordinary software, workflow automation, search, "
        "or analytics.\n"
        "Each criticism must include a concise title, concrete comment, severity, "
        "and required_fix. The required_fix should state what must be addressed, "
        "not provide rewritten copy.\n"
        "Use verdict='keep' only when the use case is strong with minor fixes; "
        "verdict='revise' when meaningful weaknesses must be fixed; and "
        "verdict='discard' when the idea is generic, unsupported, infeasible, or "
        "not a real GenAI use case.\n"
    )


def red_team_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    opportunity_map: OpportunityMapOutput,
    selected_use_cases: list[GradedUseCase],
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
    opportunity_json = json.dumps(
        opportunity_map.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    selected_json = json.dumps(
        [use_case.model_dump(mode="json") for use_case in selected_use_cases],
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Opportunity map (JSON):\n"
        f"{opportunity_json}\n\n"
        "Initial top 5 selected use cases to red-team (JSON):\n"
        f"{selected_json}\n\n"
        "Return exactly 5 reviews: one per selected use case, using the matching "
        "use_case.id as use_case_id. Each review must include at least one "
        "criticism and a verdict. Critique only: do not rewrite use cases and do "
        "not create replacement ideas."
    )


def refiner_system_prompt() -> str:
    return (
        "You are a GenAI use-case refinement editor. Given company context, the "
        "initial top 5 graded use cases, and red-team criticism, return exactly "
        "5 refined use cases: one refinement per selected original.\n"
        "Use the red-team feedback directly. Fix high-severity issues wherever "
        "the supplied evidence and context support a safe fix. Make the company "
        "fit more specific, the solution more feasible and concrete, and the "
        "expected impact more operationally specific.\n"
        "Preserve evidence: every source URL from the original selected use case "
        "must remain in the refined use case's evidence_sources. You may copy "
        "additional source URLs only from the supplied company profile, pain "
        "points, opportunity map, or selected use cases. Do not invent source "
        "URLs or unsupported facts.\n"
        "For each item, set original_use_case_id to the original use_case.id, "
        "return a complete refined_use_case object, list concrete changes_made, "
        "and keep unresolved_concerns explicit when a criticism cannot be safely "
        "fixed from the provided evidence."
    )


def refiner_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    opportunity_map: OpportunityMapOutput,
    selected_use_cases: list[GradedUseCase],
    red_team: RedTeamOutput,
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
    opportunity_json = json.dumps(
        opportunity_map.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    selected_json = json.dumps(
        [use_case.model_dump(mode="json") for use_case in selected_use_cases],
        indent=2,
        ensure_ascii=False,
    )
    red_team_json = json.dumps(
        red_team.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Opportunity map (JSON):\n"
        f"{opportunity_json}\n\n"
        "Initial top 5 selected use cases to refine (JSON):\n"
        f"{selected_json}\n\n"
        "Red-team review to address (JSON):\n"
        f"{red_team_json}\n\n"
        "Return exactly 5 refined_use_cases: one per selected use case. Each "
        "item must reference the matching original use_case.id in "
        "original_use_case_id, include a complete refined_use_case object, list "
        "changes_made, and include unresolved_concerns. Preserve all original "
        "evidence_sources URLs in the refined use case, fix supported criticisms, "
        "and leave unsafe or unsupported fixes as unresolved concerns."
    )


def final_reporter_system_prompt() -> str:
    return (
        "You are a senior GenAI strategy consultant writing the final client-ready "
        "report from a completed use-case discovery workflow.\n"
        "Return only structured data matching the requested schema. Do not write "
        "markdown as the primary output.\n"
        "The report must contain exactly 3 use cases, ranked 1-3 in the same order "
        "as the final selection. Use concise, client-ready language for executives "
        "and business owners.\n"
        "Explain the methodology using only the supplied artifacts: company "
        "research, pain-point profiling, opportunity mapping, scoring, "
        "refinement, and final top-3 selection. "
        "For every use case, include the score breakdown, why it is specific to "
        "this company, why it is high-impact, why it is iconic, implementation "
        "feasibility notes, risks, caveats, and source URLs.\n"
        "Use only facts, source URLs, and scores from the supplied JSON. Do not "
        "invent new source URLs. Source URLs must be full URL strings copied from "
        "the inputs.\n"
    )


def final_reporter_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    opportunity_map: OpportunityMapOutput,
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
    opportunity_json = json.dumps(
        opportunity_map.model_dump(mode="json"),
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
        "Opportunity map (JSON):\n"
        f"{opportunity_json}\n\n"
        "Final top 3 selected use cases with scores (JSON):\n"
        f"{final_selection_json}\n\n"
        "Write the final client-ready report. Return exactly 3 top_3_use_cases, "
        "one for each selected use case, preserving the final-selection order as "
        "rank 1, rank 2, and rank 3. For each report use case, copy the graded "
        "score object into score, summarize the solution in a one_liner, copy or "
        "condense target_users, business_problem, why_this_company, genai_solution, "
        "required_data, expected_impact, why_iconic, feasibility_notes, and risks "
        "from the selected use case, and set source_urls from its evidence_sources. "
        "Also provide company_name, executive_summary, company_context, "
        "methodology, caveats, and report-level source_urls. The methodology must "
        "explain the scoring and refinement loop. Do not add markdown formatting "
        "or any Mistral/vendor-fit discussion."
    )


def markdown_reporter_system_prompt() -> str:
    return (
        "You are a senior GenAI strategy consultant writing the client-ready "
        "markdown deliverable from an already structured final report JSON.\n"
        "Return only structured data matching the requested schema. The `markdown` "
        "field must contain the complete markdown report.\n"
        "Write polished, professional prose for executives and business owners. "
        "Make the report feel like a finished consulting deliverable, not a raw "
        "data dump. Use clear markdown structure: title, executive summary, "
        "company context, methodology, ranked recommendations, implementation "
        "considerations, caveats, and sources.\n"
        "Leverage the structure of the input JSON. Preserve the rank order and "
        "include all three recommended use cases with their score totals and "
        "important score breakdowns. Make each use case easy to scan with business "
        "problem, proposed GenAI solution, why it fits the company, expected "
        "impact, required data, feasibility, risks, and supporting sources.\n"
        "Use only facts, caveats, scores, and source URLs from the supplied JSON. "
        "Do not invent new facts, metrics, timelines or source URLs. Keep source "
        "URLs as full URLs copied from the input."
    )


def markdown_reporter_user_prompt(final_report: FinalReport) -> str:
    final_report_json = json.dumps(
        final_report.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Structured final report JSON:\n"
        f"{final_report_json}\n\n"
        "Write the final client-ready markdown report in the `markdown` field. "
        "Use the JSON as the source of truth. Start with a concise H1 title for "
        "the company, then write a polished executive summary, company context, "
        "methodology, ranked top-3 recommendations, caveats, and sources. "
        "Use professional markdown formatting with headings, bullets, and tables "
        "where useful, but do not include raw JSON or unsupported claims."
    )
