from src.core.schemas import (
    CompanyProfileOutput,
    FinalSelectionOutput,
    GradedUseCase,
    PilotKPI,
    ReportNarratives,
    UseCaseScore,
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


# ---------------------------------------------------------------------------
# Narrative-only LLM prompt (small, fast call)
# ---------------------------------------------------------------------------


def narrative_system_prompt() -> str:
    return (
        "You are writing selected prose sections for a client-facing GenAI "
        "opportunity report. Write like a practical decision memo for the "
        "company's leadership team.\n\n"
        "RULES:\n"
        "- Use only facts and URLs from the evidence brief. Do not supplement "
        "with general knowledge. Every URL must appear in the evidence brief.\n"
        "- Copy financial figures and dates exactly as they appear in the "
        "research text, including the reporting period and whether the number "
        "is a reported actual or a target. Do not round, reinterpret, or drop "
        "qualifiers. When the research gives a specific month and year for an "
        "event, preserve both — do not generalize to just a year.\n"
        "- Cite factual claims with adjacent markdown links like [source](URL).\n"
        "- Do not invent facts, URLs, ROI, timelines, or numeric targets.\n"
        "- Do not state that a deal or acquisition is completed unless the "
        "source explicitly confirms completion.\n"
        "- In `company_context`, lead with the most strategically significant "
        "developments. Do not write a generic company profile.\n"
        "- In each `opportunity_blurbs` entry, weave together the business "
        "problem, company fit, and what makes the idea iconic and "
        "non-transferable. Do not create separate iconicness language.\n"
        "- In `decision_rationales`, write one sentence per use case mentioning "
        "what is distinctive. When scores show weak iconicness, note why the "
        "recommendation is limited.\n"
        "- In `limitations`, name specific data gaps — missing internal cost "
        "data, unverified regulatory timelines, press-release figures without "
        "breakdowns. Do not write meta-commentary about report methodology."
    )


def narrative_user_prompt(
    company_profile: CompanyProfileOutput,
    final_selection: FinalSelectionOutput,
) -> str:
    use_case_sections: list[str] = []
    for rank, item in enumerate(final_selection.selected, start=1):
        uc = item.use_case
        lines = [
            f"### Rank {rank}: {uc.title}",
            f"- Target users: {', '.join(uc.target_users)}",
            f"- Fit score: {item.score.weighted_total:.1f}/10",
            f"- Business problem: {uc.business_problem}",
            f"- Company fit: {uc.why_this_company}",
            f"- Iconicness: {uc.why_iconic}",
            "- Grader rubric:",
            *_grader_rubric_brief_lines(item.score),
            "- Evidence sources:",
            *[f"  - [source]({src})" for src in uc.evidence_sources],
        ]
        use_case_sections.append("\n".join(lines))

    evidence = (
        f"## Company: {company_profile.company_name}\n\n"
        "## Sourced company research\n"
        f"{company_profile.research_text}\n\n"
        "## Selected use cases\n" + "\n\n".join(use_case_sections)
    )
    return (
        f"{evidence}\n\n"
        "Write the `company_context`, `opportunity_blurbs` (one per use case "
        "in rank order), `decision_rationales` (one sentence each), and "
        "`limitations` (2-3 bullet points)."
    )


# ---------------------------------------------------------------------------
# Programmatic report assembly
# ---------------------------------------------------------------------------


def _scoring_table(score: UseCaseScore) -> str:
    rows = [
        ("Company relevance", score.company_relevance),
        ("Business impact", score.business_impact),
        ("Iconicness", score.iconicness),
        ("GenAI fit", score.genai_fit),
        ("Feasibility", score.feasibility),
        ("Evidence strength", score.evidence_strength),
    ]
    lines = [
        "| Dimension | Rationale | Score (/10) |",
        "| --- | --- | --- |",
    ]
    for label, dim in rows:
        lines.append(f"| {label} | {dim.rationale} | {dim.score} |")
    return "\n".join(lines)


def _kpi_paragraph(kpi: PilotKPI) -> str:
    direction = kpi.target_direction.replace("_", " ")
    return (
        f"- **{kpi.kpi}** matters because {kpi.why_it_matters} "
        f"Measure it with {kpi.measurement_method} "
        f"Baseline source: {kpi.baseline_source}; target direction is {direction}."
    )


def _use_case_section(
    rank: int,
    item: GradedUseCase,
    opportunity_blurb: str,
) -> str:
    uc = item.use_case
    score = item.score

    risk_lines = [f"- {risk}" for risk in uc.risks]

    kpi_lines = [_kpi_paragraph(kpi) for kpi in uc.pilot_kpis]

    return "\n\n".join(
        [
            f"## {rank}. {uc.title}",
            f"### The Opportunity\n\n{opportunity_blurb}",
            f"### Scoring (1–10)\n\n{_scoring_table(score)}",
            "### How The Workflow Would Work\n\n" + uc.genai_solution,
            f"### Why GenAI Fits\n\n{uc.genai_mechanism.genai_vs_classical}",
            "### Data and Integration Needs\n\n"
            + "\n".join(f"- {item}" for item in uc.required_data),
            "### Impact To Validate\n\n" + "\n".join(kpi_lines),
            "### Risks and Mitigations\n\n" + "\n".join(risk_lines),
        ]
    )


def _summary_table(
    final_selection: FinalSelectionOutput,
    decision_rationales: list[str],
) -> str:
    lines = [
        "| Rank | Opportunity | Primary users | Fit score (/10) | Decision rationale |",
        "| --- | --- | --- | --- | --- |",
    ]
    for rank, (item, rationale) in enumerate(
        zip(final_selection.selected, decision_rationales), start=1
    ):
        uc = item.use_case
        users = ", ".join(uc.target_users)
        fit = f"{item.score.weighted_total:.1f}/10"
        lines.append(f"| {rank} | {uc.title} | {users} | {fit} | {rationale} |")
    lines.append("")
    lines.append(
        "> **Fit score** = 25% iconicness + 25% GenAI fit + 20% business impact"
        " + 15% company relevance + 10% feasibility + 5% evidence strength"
    )
    return "\n".join(lines)


def _sources_section(final_selection: FinalSelectionOutput) -> str:
    seen: set[str] = set()
    links: list[str] = []
    for item in final_selection.selected:
        for url in item.use_case.evidence_sources:
            if url not in seen:
                seen.add(url)
                links.append(f"- [{url}]({url})")
    return "\n".join(links)


def build_report_markdown(
    company_profile: CompanyProfileOutput,
    final_selection: FinalSelectionOutput,
    narratives: ReportNarratives,
) -> str:
    sections = [
        f"# GenAI Opportunity Report — {company_profile.company_name}",
        f"## Company Context\n\n{narratives.company_context}",
        "## Recommended Opportunities\n\n"
        + _summary_table(final_selection, narratives.decision_rationales),
    ]

    for rank, (item, blurb) in enumerate(
        zip(final_selection.selected, narratives.opportunity_blurbs), start=1
    ):
        sections.append(_use_case_section(rank, item, blurb))

    limitations_text = "\n".join(f"- {lim}" for lim in narratives.limitations)
    sections.append(f"## Limitations\n\n{limitations_text}")
    sections.append(f"## Sources\n\n{_sources_section(final_selection)}")

    return "\n\n".join(sections)
