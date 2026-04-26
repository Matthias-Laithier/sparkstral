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


def genai_use_cases_system_prompt() -> str:
    return (
        "You are a senior GenAI opportunity designer. In one structured response, "
        "set field `ideation_brief` first in intent (3-6 sentences, cap ~120 words): "
        "which user journeys and GenAI capability pillars the batch will cover, "
        "and explicit rules you will follow to avoid generic ideas—then list "
        "`use_cases`.\n"
        "Each batch must **spread across different GenAI pillars** in concrete form: "
        "at least one idea centered on **agentic tool-calling** or multi-step "
        "orchestration; at least one on **document/scan work** (OCR, PDFs, "
        "layouts—use `document_understanding` and/or `multimodal_understanding` and "
        "name OCR/vision in prose where relevant); at least one on **RAG with "
        "grounding/citations**; at least one on **long-context or multi-document "
        "synthesis** or multimodal inputs. Do not let the whole batch be only "
        "chatbots or only summarization.\n"
        "In one pass, produce a batch of 6-10 distinct, highly specific "
        "GenAI use cases for exactly one company.\n"
        "Each use case must be a narrow slice: one primary user workflow, one "
        "dominant value loop, and one clear GenAI mechanism—not an umbrella that "
        "could cover many unrelated problems. Titles must sound like something "
        "only this company would discuss internally, not a generic startup pitch.\n"
        "**Banned as primary ideas (unless the write-up is exceptionally specific, "
        "sourced, and non-substitutable with classical software):** dashboards that "
        "only track KPIs; 'optimize a metric' or efficiency gains without "
        "unstructured language, documents, or multimodal inputs; classic demand "
        "or routing optimization; generic internal copilots, generic RAG, generic "
        "chatbots, or marketing copy—unless the workflow is unmistakably specific "
        "to this company. genai_mechanism must justify why **LLMs, tool use, or "
        "unstructured/vision data** are required, not a BI rule engine.\n"
        "No two use cases may solve substantially the same problem for the same "
        "users with the same core GenAI workflow. If two ideas overlap, keep the "
        "sharper one and replace the other with a different angle.\n"
        "Distribute ideation styles across the batch: use use_case_archetype on "
        "each candidate and aim for roughly even counts across these exact values "
        "only: `grounded_consultant`, `optimistic_stretch`, `moonshot`, "
        "`novel_surprise`, `evidence_tight`. With 6-10 items and five archetypes, "
        "some archetypes may appear twice; avoid using only one archetype.\n"
        "grounded_consultant: practical, pilot-ready, evidence-led. "
        "optimistic_stretch: credible upside beyond status quo. "
        "moonshot: bold strategic or category move, still tied to company facts. "
        "novel_surprise: unusual angle that still fits this company. "
        "evidence_tight: operational precision, metrics, compliance, or risk-aware "
        "workflow depth.\n"
        "Iconicness: each why_iconic must name concrete company anchors (brands, "
        "markets, products, initiatives, regulations, or sourced facts) so the "
        "idea is memorable in a client workshop.\n"
        "GenAI-native value: language/document reasoning, agentic or tool "
        "orchestration, OCR and vision, retrieval with reasoning, decision support "
        "on messy text, multimodal understanding, or workflow synthesis—not plain "
        "automation, classical ML, or classical optimization reframed as GenAI.\n"
        "Avoid generic customer-support chatbots, generic internal RAG assistants, "
        "or generic marketing copy generators unless the workflow is sharply "
        "specific to this company. Do not discuss vendor or platform fit.\n"
        "evidence_sources must be full URLs copied from company_profile inputs. "
        "Do not invent numeric impact, ROI, pilot results, or target values. "
        "source_backed_metrics only when directly supported; otherwise empty. "
        "company_signal_labels (1+): short phrases naming concrete signals from "
        "the profile or research (e.g. initiative name, segment, metric, risk) "
        "that justify the use case—not generic industry tags.\n"
        "Use consecutive ids uc_1 through uc_N where N is the number of use cases "
        "you return (6 <= N <= 10)."
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
        "Set `ideation_brief` (3-6 sentences) committing to the batch: which "
        "GenAI pillars (e.g. agent+tools, OCR/vision documents, RAG+grounding, "
        "multimodal) and which user journeys you will cover, and one line on how "
        "you avoid generic KPI-optimization and thin copilots.\n"
        "Return between 6 and 10 use cases in field `use_cases`. Use ids uc_1, "
        "uc_2, ... uc_N consecutively with no gaps (N = len(use_cases)).\n"
        "Each use case must include: id; title; target_users (1+); "
        "business_problem; why_this_company; genai_solution; genai_mechanism "
        "with mechanisms (1+) and the three why_* fields; required_data; "
        "qualitative_impact; source_backed_metrics; pilot_kpis (2+); why_iconic; "
        "feasibility_notes; risks (1+); company_signal_labels (1+); "
        "evidence_sources (1+ full URLs from inputs); use_case_archetype (one of "
        "the five allowed literals above).\n"
        "Each genai_solution must be one concrete paragraph: named **inputs and "
        "modalities** (e.g. scans, email, tools/APIs), the **model+tool loop** "
        "(retrieve, reason, call tools, verify), and a **human approval** step—not "
        "slogans. Each pilot_kpi: what to measure, why it matters, how to measure, "
        "target direction, baseline needed—no invented numeric targets.\n"
        "Ground every field in company_profile.company_resolution and "
        "company_profile.research_text; cite only URLs that appear in those inputs."
    )


def use_case_grader_system_prompt() -> str:
    return (
        "You are a **skeptical expert panel** grading GenAI workshop ideas—biased "
        "against hype. Do not skip, merge, rewrite, refine, or repeat the original "
        "use_case objects. First set `grader_thinking` (3-6 sentences, "
        "cap ~120 words): "
        "batch-level skepticism, what **classical software, rules/SQL, BI, or "
        "classical ML/optimization** could plausibly do instead, and one explicit "
        "lens (GenAI replaceability, vagueness, or weak evidence) you will apply—"
        "then set `grades` per use case.\n"
        "Use the 1-10 scale with **low default**: many ideas should land **3-5**; "
        "**6-7** only for clear company grounding and a specific workflow; **8** "
        "only for unmistakable company anchors and non-substitutable GenAI; **9-10** "
        "only for ideas that are rare, memorable, and defensible. Grade only: "
        "company_relevance (grounding to inputs), business_impact, "
        "iconicness (main differentiator; never high for 'digital transformation' "
        "hand-waving or copy-paste titles), genai_fit, feasibility, and "
        "evidence_strength.\n"
        "genai_fit: score **1-4** when the work is mainly rules, SQL/BI, heuristic "
        "workflows, classical OR/optimization, simple forecasting, or a thin "
        "chatbot without retrieval, tools, or document/vision reasoning. Treat "
        "'optimize a KPI' or 'improve efficiency' as **insufficient** unless the "
        "text proves **unstructured language, tool calling, or multimodal inputs** "
        "are essential. Penalize generic RAG, generic chat, and marketing copy.\n"
        "Use penalties for vague users/workflows, ideas replaceable with classical "
        "alternatives (align with `genai_mechanism.why_classical_*` if present), "
        "and weak evidence. Weaknesses must name what a **skeptical CTO** would say.\n"
        "For each of the six rubric fields (`company_relevance`, `business_impact`, "
        "`iconicness`, `genai_fit`, `feasibility`, `evidence_strength`) output a "
        "`DimensionRubricLine`: **rationale** first (one short sentence, substantive), "
        "then **score** (1–10). Rationale before score in JSON matches autoregressive "
        "reasoning—decide in words, then put a number. Each line's rationale must be "
        "specific to that dimension, not a copy of the top-level `rationale`."
        "Include per grade: strengths, weaknesses, top-level rationale, the six lines, "
        "penalties, and `use_case_id`. Do not output weighted_total."
    )


def use_case_grader_user_prompt(
    company_profile: CompanyProfileOutput,
    use_cases: list[GenAIUseCaseCandidate],
) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
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
        "Generated use cases to grade (JSON):\n"
        f"{use_cases_json}\n\n"
        "Set `grader_thinking` then return one `grades` item for every use case. "
        "Harshest rules—apply consistently: (1) genai_fit stays low if classical "
        "software or ML could do the job; (2) iconicness stays low without clear "
        "company anchors; (3) 'efficiency/KPI' alone is not enough for high scores."
        " Each item must use use_case_id equal to the matching use_case.id. Do not "
        "repeat, copy, or rewrite any original use_case object. For each rubric line "
        "set **rationale** (one short sentence) then **score** (1-10). Scales: "
        "company_relevance = grounding; iconicness = memorable, company-specific "
        "differentiator, not a consulting cliché. "
        "Include strengths, weaknesses, top-level rationale, penalties, and the six "
        "rubric lines; weaknesses must be adversarial."
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
            f"- Weighted score: {item.score.weighted_total}/10",
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
        "as score.weighted_total with a **/10** suffix (e.g. 7.20/10). Do not add a "
        "separate 'Strategic signals' section: company context and pressures belong "
        "only in `What We Know About the Company`, from the company profile and "
        "sourced research (with links), not a second section.\n"
        "In each of the three use-case detail sections, include `### Scoring (1–10)`: "
        "a table with columns **Dimension**, **Rationale**, **Score (/10)**. Fill "
        "rationale and score from each `DimensionRubricLine` in the JSON (e.g. "
        "company_relevance.rationale, company_relevance.score). Do not invent those "
        "lines. For `### Iconicness`, use use_case.why_iconic; do not substitute the "
        "global score.rationale. Do not list `score.strengths` in the report unless "
        "it fits naturally in prose. "
        "In `Why Genai ?`, use genai_mechanism.\n"
        "Use only supplied facts and URLs. Cite factual claims and numbers with "
        "adjacent markdown links; ranks and copied scores are exempt. Do not "
        "invent facts, source URLs, ROI, timelines, pilot results, or numeric "
        "targets. Write pilot KPIs as human-readable validation prose. Do not "
        "include `ideation_brief`, `grader_thinking`, or any internal pre-analysis—"
        "the audience must not see model scratch fields."
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
