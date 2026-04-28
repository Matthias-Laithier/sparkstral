import json
from pathlib import Path

from src.core.schemas import CompanyProfileOutput, FinalSelectionOutput

from .grading import _grader_rubric_brief_lines

MARKDOWN_REPORT_TEMPLATE = (
    Path(__file__).parent.parent / "templates" / "genai_use_case_report.md"
).read_text(encoding="utf-8")


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
        "it as a verified figure. "
        "Do not state that a deal, acquisition, or project is completed unless "
        "the source explicitly confirms completion — use 'announced', 'agreed "
        "to acquire', or 'expected to close by [date]' when the source does "
        "not confirm closure. Write "
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
