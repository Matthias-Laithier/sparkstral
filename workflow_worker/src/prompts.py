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


def company_context(profile: CompanyProfileOutput) -> str:
    resolution_json = json.dumps(
        profile.company_resolution.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (resolved identity + sourced research):\n\n"
        "Resolved company identity (JSON):\n"
        f"{resolution_json}\n\n"
        "Sourced company research text:\n"
        f"{profile.research_text}"
    )


def pain_point_system_prompt() -> str:
    return (
        "You are an analyst. Given a company_profile containing a resolved company "
        "identity and sourced company research text, extract major pain points, "
        "industry gaps, unmet needs, opportunity pressures, and opportunity "
        "hypotheses relevant to the company and its field.\n"
        "Only include pain points and opportunities supported by the supplied "
        "company_profile research text or resolver evidence URLs. Assign pain point "
        "prominence 1-10 from the evidence strength and business impact. Every "
        "source must be a full URL string copied from the supplied inputs. Do not "
        "add new web research, invent unsupported industry generalizations, or cite "
        "URLs not present in the profile."
    )


def pain_point_user_prompt(
    profile: CompanyProfileOutput,
) -> str:
    return (
        f"{company_context(profile)}\n\n"
        "Return 3-8 pain points and 3-8 opportunities derived only from this "
        "company_profile. Use the sourced research sections about business lines, "
        "customers, strategic priorities, operational pain points, regulatory "
        "pressure, customer/market pressure, growth opportunities, and technology "
        "transformation directly. Be specific, avoid duplication, and copy each "
        "source URL from company_profile.company_resolution.evidence or "
        "company_profile.research_text. Each opportunity must link to one or more "
        "pain point titles and describe a different way to address or exploit the "
        "pressure behind those pain points."
    )


PERSONA_GUIDANCE: dict[GenAIUseCasePersona, str] = {
    "grounded consultant": (
        "Stay practical, evidence-led, and implementation-aware, but do not settle "
        "for ordinary automation. Prefer signature operational workflows that a "
        "serious client team could pilot with known data and approval paths while "
        "still feeling high-impact and specific to this company. Keep iconicness "
        "in mind."
    ),
    "moonshot strategist": (
        "Think ambitiously and optimistically about strategic advantage. Propose "
        "category-defining ideas that are bold, memorable, and commercially "
        "important while still grounded in the supplied company facts, pain "
        "points, and GenAI-native mechanisms. Keep iconicness in mind."
    ),
    "why not? inventor": (
        "Look for unusual, surprising, and novel ideas. Push beyond default "
        "consulting recommendations toward distinctive concepts that could only "
        "make sense in this company's context, while making feasibility tradeoffs "
        "explicit. Keep iconicness in mind."
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
        "Produce exactly 3 meaningfully varied, company-specific GenAI use cases "
        "that feel iconic for this company, not interchangeable with any other "
        "business.\n"
        f"Every candidate must set ideation_lens exactly to `{ideation_lens}`. "
        f"Use exactly these IDs, one per candidate: {expected_ids}. Do not use "
        "any other ID format.\n"
        "Ground every use case in the resolved company identity, sourced company "
        "research text, pain points, opportunities, and evidence URLs. Name "
        "concrete workflows, data, users, and why_iconic.\n"
        "The core value must be GenAI-native: language/document reasoning, "
        "generation, tool orchestration, decision support, multimodal "
        "understanding, or workflow synthesis. Reframe ideas that could be done "
        "with ordinary software or classical ML.\n"
        "Avoid overused generic product ideas, including "
        "generic customer support chatbot, internal knowledge assistant or RAG "
        "for documents, or generic marketing copy generators unless the concept "
        "is deeply specific to this company. Do not discuss vendor or platform "
        "fit.\n"
        "evidence_sources must be full URLs copied from prior inputs. Do not "
        "invent numeric impact, ROI, pilot results, or target values. Use "
        "source_backed_metrics only for metrics directly supported by evidence; "
        "otherwise leave it empty and use pilot_kpis for what to validate."
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
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "Pain point and opportunity analysis (JSON):\n"
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
        "approval step exists. Use company_profile.company_resolution, "
        "company_profile.research_text, pain points, opportunities, business lines, "
        "strategic priorities, and evidence URLs directly. "
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
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "Pain point and opportunity analysis (JSON):\n"
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
        "You strictly grade every provided GenAI use case. Do not skip, merge, "
        "rewrite, refine, or repeat the original use_case objects.\n"
        "Use the full 1-10 scale: bad ideas 1-3, ordinary ideas 4-6, strong ideas 7-8, "
        "rare exceptional ideas 9-10. Grade only these dimensions: company_relevance "
        "(grounding), business_impact, iconicness (main differentiator), "
        "genai_fit, feasibility, and evidence_strength.\n"
        "Penalize generic chatbots, generic RAG/search, marketing generators, "
        "classical ML/optimization ideas, unsupported metrics, weak evidence, "
        "vague users, unclear workflows, missing data paths, and unclear human "
        "approval. Include strengths, weaknesses, rationale, penalties, and "
        "use_case_id. Do not output weighted_total."
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
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "Pain point and opportunity analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Generated use cases to grade (JSON):\n"
        f"{use_cases_json}\n\n"
        "Return one grades item for every use case above. Each item must use "
        "use_case_id equal to the matching use_case.id. Do not repeat, copy, "
        "or rewrite any original use_case object. Grade strictly using only "
        "the six rubric fields on the 1-10 scale: "
        "company_relevance, business_impact, iconicness, genai_fit, feasibility, "
        "and evidence_strength. Treat company_relevance as a grounding check and "
        "iconicness as the main differentiator. Include strengths, weaknesses, "
        "rationale, and penalties for each use case."
    )


def _source_links(sources: list[str]) -> str:
    return " ".join(f"[source]({source})" for source in sources)


def markdown_report_evidence_brief(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    resolution = company_profile.company_resolution
    resolution_lines = [
        f"- Resolved company: {resolution.resolved_name}",
        f"- Website: {resolution.website}",
        f"- Headquarters country: {resolution.headquarters_country}",
        f"- Primary industry: {resolution.primary_industry}",
        f"- Ambiguity notes: {resolution.ambiguity_notes}",
    ]
    resolution_lines.extend(
        f"- {item.claim} [source]({item.source})" for item in resolution.evidence
    )
    pain_point_lines = [
        "- "
        f"{pain_point.title}: {pain_point.description} "
        f"(prominence {pain_point.prominence}/10) "
        f"{_source_links(pain_point.sources)}"
        for pain_point in pain_points.pain_points
    ]
    opportunity_lines = [
        "- "
        f"{opportunity.title}: {opportunity.description} "
        f"(linked pain points: {', '.join(opportunity.linked_pain_points)}) "
        f"{_source_links(opportunity.sources)}"
        for opportunity in pain_points.opportunities
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
            (
                f"- Iconicness: {use_case.why_iconic} "
                f"(score {item.score.iconicness}/10; rationale: "
                f"{item.score.rationale})"
            ),
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

        use_case_sections.append("\n".join(lines))

    resolution_text = "\n".join(resolution_lines)
    pain_points_text = "\n".join(pain_point_lines)
    opportunities_text = "\n".join(opportunity_lines)
    use_cases_text = "\n\n".join(use_case_sections)

    return (
        "Citation-ready evidence brief:\n\n"
        "## Resolved company identity\n"
        f"{resolution_text}\n\n"
        "## Sourced company research\n"
        f"{company_profile.research_text}\n\n"
        "## Pain points\n"
        f"{pain_points_text}\n\n"
        "## Opportunities linked to pain points\n"
        f"{opportunities_text}\n\n"
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
        "Use the selected top 3 in order; copy score.weighted_total into the "
        "ranked table. Discuss pain points and opportunity themes from the "
        "pain-point analysis. Discuss Iconicness from use_case.why_iconic and "
        "score.iconicness. In `Why Genai ?`, use genai_mechanism.\n"
        "Use only supplied facts and URLs. Cite factual claims and numbers with "
        "adjacent markdown links; ranks and copied scores are exempt. Do not "
        "invent facts, source URLs, ROI, timelines, pilot results, or numeric "
        "targets. Write pilot KPIs as human-readable validation prose."
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
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
        "Pain point and opportunity analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Selected top 3 use cases with scores (JSON):\n"
        f"{final_selection_json}\n\n"
        "Write the final markdown report in the `markdown` field. Use the evidence "
        "brief for citation links and the JSON as source of truth. Do not include "
        "raw JSON."
    )
