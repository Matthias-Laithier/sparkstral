import json
from datetime import date
from pathlib import Path

from src.schemas import (
    CompanyProfileOutput,
    CompanyResolutionOutput,
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
        "title, section name, or faithful source detail supporting the claim; "
        "Source role: one of `company_primary`, `filing_or_investor`, "
        "`official_press_release`, `regulator_or_government`, "
        "`wire_or_business_media`, `industry_source`, `background_only`, or "
        "`uncertain`; Support directness: one of `direct`, `partial`, or "
        "`background`. "
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
        "Do not use hardcoded domain reputation, allowlists, or blocklists; assign "
        "source role and support directness from the source context, publisher "
        "type, and how directly the citation supports the exact claim. "
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


def genai_use_cases_system_prompt() -> str:
    return (
        "You are a senior GenAI opportunity designer. Create 6-10 narrow, "
        "client-workshop-worthy use cases for one company.\n"
        "First write `ideation_brief` (3-6 sentences, cap ~120 words): name the "
        "company anchors you will use, the capability spread, and what you rejected "
        "as too generic. Then write `use_cases` with consecutive ids uc_1...uc_N.\n"
        "Quality bar: every candidate needs one specific workflow, one value loop, "
        "one GenAI mechanism, and a title anchored in sourced company context. "
        "Use reusable anchor types only: named assets, initiatives, geographies, "
        "regulations, customer segments, operating models, products, pressures, or "
        "workflow bottlenecks. Do not steer toward any preselected idea.\n"
        "Discard candidates that would likely score below 7/10 on iconicness: "
        "the title and `why_iconic` must explain why the idea is not a peer-company "
        "template after a name swap. If the differentiator is only "
        "'digital transformation', efficiency, a broad chatbot, generic RAG, "
        "a dashboard, or classical optimization with GenAI branding, drop it.\n"
        "Capability spread: include agentic tool use or orchestration, document or "
        "multimodal understanding, grounded RAG, embeddings, and long-context or "
        "multi-document synthesis across the batch. Avoid a batch of only chatbots "
        "or summaries.\n"
        "GenAI must add value through messy language, documents, images, conflicting "
        "context, retrieval with reasoning, tool use, structured drafting, or "
        "human-reviewable decisions. Say what classical software or ML should still "
        "handle; never claim it is categorically incapable.\n"
        "Use the archetypes `grounded_consultant`, `optimistic_stretch`, `moonshot`, "
        "`novel_surprise`, and `evidence_tight` with no single archetype dominating. "
        "No two use cases may share the same users, problem, and core GenAI workflow.\n"
        "Use only facts and URLs from the supplied company profile. Prefer direct, "
        "high-quality evidence for major claims; treat weak support as a caveat. "
        "Do not invent numeric impact, ROI, pilot results, or targets. "
        "`source_backed_metrics` is empty unless a metric is directly sourced."
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
        "Return `ideation_brief` and 6-10 `use_cases` with ids uc_1...uc_N.\n"
        "Required per use case: id; title; target_users (1+); business_problem; "
        "why_this_company; genai_solution; genai_mechanism including mechanisms "
        "(1+), why_genai_is_needed, genai_advantage_over_classical_software, "
        "genai_advantage_over_classical_ml; required_data; qualitative_impact; "
        "source_backed_metrics; pilot_kpis (2+); why_iconic; feasibility_notes; "
        "risks (1+); company_signal_labels (1+); evidence_sources (1+ URLs from "
        "inputs); use_case_archetype (one of the five literals).\n"
        "For each candidate, make `genai_solution` one concrete paragraph covering "
        "inputs/modalities, model+tool loop, generated output, and human approval. "
        "Each pilot KPI must state what to measure, why it matters, measurement "
        "method, baseline, and target direction without numeric targets.\n"
        "Candidate inclusion test: the title names a company anchor; `why_iconic` "
        "makes a non-transferability argument; and the workflow shows where GenAI "
        "changes expert judgment rather than merely automating a generic process. "
        "Ground every field in company_resolution and research_text; URLs only from "
        "those inputs."
    )


def use_case_grader_system_prompt() -> str:
    return (
        "You are a skeptical expert panel grading one GenAI workshop idea. Do not "
        "rewrite, merge, skip, or repeat the original use_case. Set "
        "`grader_thinking` first (3-6 sentences, cap ~120 words), then exactly one "
        "`grade`.\n"
        "Use a low-default 1-10 scale: 3-5 is normal, 6-7 needs clear grounding and "
        "a specific workflow, 8 needs unmistakable company anchors and strong GenAI "
        "fit, and 9-10 is rare. Grade only company_relevance, business_impact, "
        "iconicness, genai_fit, feasibility, and evidence_strength.\n"
        "Report-worthy test: would this feel specific and memorable in front of the "
        "company's leadership, or like a peer-company template? If it fails, cap "
        "iconicness at 5 and also constrain adjacent scores that rely on the same "
        "weakness: business_impact for generic value, genai_fit for classical "
        "automation in disguise, and evidence_strength for vague or weak anchors.\n"
        "GenAI fit is low when rules, SQL/BI, classical ML, forecasting, routing, "
        "optimization, or a thin chatbot could do the core job. Reward GenAI only "
        "where unstructured or multimodal input, retrieval with reasoning, tool "
        "use, drafting, explanation, or human-reviewable decisions are central. "
        "Separate what GenAI adds from what classical systems should still handle.\n"
        "Use penalties for peer overlap, vague users or workflows, weak evidence, "
        "generic titles, and `why_iconic` text that only says the idea aligns with "
        "strategy. Compare peer summaries; if the same users, problem, and GenAI "
        "workflow recur, name the overlapping use_case_id in penalties.\n"
        "For each rubric field, output a `DimensionRubricLine` with a specific "
        "one-sentence rationale before the score. Include strengths, adversarial "
        "weaknesses, top-level rationale, penalties, and `use_case_id`. Do not "
        "output weighted_total."
    )


def grade_single_use_case_user_prompt(
    company_profile: CompanyProfileOutput,
    use_case: GenAIUseCaseCandidate,
    peer_summaries: list[str],
) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
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
        "Company profile (resolved identity + sourced research JSON):\n"
        f"{company_json}\n\n"
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
            f"- Iconicness (narrative for the report's Iconicness section): "
            f"{use_case.why_iconic}",
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
        lines.append(f"- Archetype: {use_case.use_case_archetype}")

        use_case_sections.append("\n".join(lines))

    resolution_text = "\n".join(resolution_lines)
    use_cases_text = "\n\n".join(use_case_sections)

    return (
        "Citation-ready evidence brief:\n\n"
        "## Resolved company identity\n"
        f"{resolution_text}\n\n"
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
        "is limited. Do not add a separate 'Strategic signals' section.\n"
        "In each of the three use-case detail sections, include `### Scoring (1–10)`: "
        "a table with columns **Dimension**, **Rationale**, **Score (/10)**. Fill "
        "rationale and score from the JSON `DimensionRubricLine`s; do not invent "
        "them. For `### Iconicness`, use use_case.why_iconic. Do not upgrade a "
        "generic use case with new branding language; reflect low iconicness "
        "honestly instead of polishing it into a signature concept. "
        "In `Why GenAI Fits`, use genai_mechanism to explain what GenAI adds "
        "and what classical systems should still handle. Avoid absolute claims "
        "such as 'classical software cannot handle X'.\n"
        "Use only supplied facts and URLs. Cite factual claims and numbers with "
        "adjacent neutral markdown links like [source](URL). Do not invent facts, "
        "source URLs, ROI, timelines, pilot results, or numeric targets. Surface "
        "weak evidence in `Caveats and Source Limits`. Write pilot KPIs as "
        "human-readable validation prose. Do not include `ideation_brief`, "
        "`grader_thinking`, raw JSON, or internal pre-analysis.\n"
        "In `## Sources`, classify each unique URL from the evidence brief using "
        "source-role and support-directness labels from the brief. Do not use "
        "domain allowlists, blocklists, regexes, or memorized publisher reputation."
    )


def markdown_reporter_user_prompt(
    company_profile: CompanyProfileOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    evidence_brief = markdown_report_evidence_brief(
        company_profile,
        final_selection,
    )
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
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
        "Selected top 3 use cases with scores (JSON):\n"
        f"{final_selection_json}\n\n"
        "Write the final markdown report in the `markdown` field. Use the evidence "
        "brief for citation links and the JSON as source of truth. Do not include "
        "raw JSON, ideation_brief, or grader_thinking."
    )
