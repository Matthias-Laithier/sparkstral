from datetime import date

from src.prompts import (
    MARKDOWN_REPORT_TEMPLATE,
    combined_research_prompt,
    company_context,
    genai_use_cases_system_prompt,
    genai_use_cases_user_prompt,
    grade_single_use_case_user_prompt,
    markdown_report_evidence_brief,
    markdown_reporter_system_prompt,
    markdown_reporter_user_prompt,
    use_case_grader_system_prompt,
    web_search_system_prompt,
)
from src.schemas import (
    CompanyProfileOutput,
    DimensionRubricLine,
    FinalSelectionOutput,
    GenAIMechanism,
    GenAIUseCaseCandidate,
    GradedUseCase,
    PilotKPI,
    SourceBackedMetric,
    UseCaseScore,
)


def _genai_mechanism() -> GenAIMechanism:
    return GenAIMechanism(
        mechanisms=["document_understanding", "structured_generation"],
        why_genai_is_needed="The workflow needs document reasoning and generation.",
        genai_advantage_over_classical_software=(
            "Rule-based systems can cover routing, while GenAI adds document "
            "reasoning over messy operational context."
        ),
        genai_advantage_over_classical_ml=(
            "Classical ML can rank known patterns, while GenAI drafts grounded "
            "recommendations with explanations."
        ),
    )


def _source_backed_metric(source_url: str) -> SourceBackedMetric:
    return SourceBackedMetric(
        label="Pain prominence",
        value="Prominence 8 of 10",
        source_url=source_url,
        source_quote_or_evidence="The source supports the pain point prominence.",
        applies_to="company",
        confidence="medium",
    )


def _pilot_kpis() -> list[PilotKPI]:
    return [
        PilotKPI(
            kpi="Manual review cycle time",
            why_it_matters="Shows whether the workflow speeds up expert review.",
            measurement_method="Compare cycle time before and during the pilot.",
            target_direction="decrease",
            baseline_needed="Current median review cycle time.",
        ),
        PilotKPI(
            kpi="Accepted recommendations",
            why_it_matters="Shows whether generated outputs are useful to reviewers.",
            measurement_method="Track reviewer acceptance rate during the pilot.",
            target_direction="increase",
            baseline_needed=(
                "Current acceptance rate for manually drafted recommendations."
            ),
        ),
    ]


def _candidate(index: int) -> GenAIUseCaseCandidate:
    evidence_source = f"https://example.com/source-{index}"
    return GenAIUseCaseCandidate(
        id=f"uc_{index}",
        title=f"Use case {index}",
        business_domain="manufacturing",
        target_users=["Ops"],
        business_problem="Problem",
        why_this_company="Company fit",
        genai_solution="Solution",
        genai_mechanism=_genai_mechanism(),
        required_data="Data",
        qualitative_impact="Qualitative impact",
        source_backed_metrics=[_source_backed_metric(evidence_source)],
        pilot_kpis=_pilot_kpis(),
        why_iconic="Iconic fit",
        feasibility_notes="Feasible with existing records",
        risks=["Risk"],
        company_signal_labels=["Pain 1", "widget_supply"],
        evidence_sources=[evidence_source],
    )


def _company_profile() -> CompanyProfileOutput:
    return CompanyProfileOutput(
        company_name="Acme",
        research_text=(
            "**Business Lines & Customer Segments**\n"
            "- Claim: Acme makes widgets.\n"
            "  Source URL: https://example.com/company\n"
            "  Citation: Company page describes widget products.\n"
            "- Claim: Acme serves industrial buyers.\n"
            "  Source URL: https://example.com/customers\n"
            "  Citation: Customer page names industrial buyers.\n\n"
            "**Strategic Priorities & Recent Initiatives**\n"
            "- Claim: Acme prioritizes operational efficiency.\n"
            "  Source URL: https://example.com/strategy\n"
            "  Citation: Strategy page lists operational efficiency.\n\n"
            "**Geography/Markets & Operational Pain Points**\n"
            "- Claim: Acme faces supply chain delays.\n"
            "  Source URL: https://example.com/pain-1\n"
            "  Citation: Annual report notes supply chain delays.\n"
            "- Claim: New safety rules affect Acme's plants.\n"
            "  Source URL: https://example.com/pain-2\n"
            "  Citation: Regulator page describes new safety rules.\n"
            "- Claim: Customers expect faster configuration support.\n"
            "  Source URL: https://example.com/pain-3\n"
            "  Citation: Publication reports faster configuration expectations.\n\n"
            "**Growth Opportunities & Technology Transformation**\n"
            "- Claim: Acme has an aftermarket service expansion opportunity.\n"
            "  Source URL: https://example.com/growth\n"
            "  Citation: Investor presentation highlights aftermarket service "
            "expansion.\n"
            "- Claim: Acme is modernizing factory systems.\n"
            "  Source URL: https://example.com/digital\n"
            "  Citation: Digital page describes factory system modernization."
        ),
    )


def _rubric_line(score: int, label: str) -> DimensionRubricLine:
    return DimensionRubricLine(rationale=f"Rationale for {label}.", score=score)


def _score(use_case_id: str) -> UseCaseScore:
    return UseCaseScore(
        use_case_id=use_case_id,
        strengths=["Strength"],
        weaknesses=["Weakness"],
        rationale="Rationale",
        company_relevance=_rubric_line(3, "company_relevance"),
        business_impact=_rubric_line(3, "business_impact"),
        iconicness=_rubric_line(3, "iconicness"),
        genai_fit=_rubric_line(3, "genai_fit"),
        feasibility=_rubric_line(3, "feasibility"),
        evidence_strength=_rubric_line(3, "evidence_strength"),
        penalties=[],
        weighted_total=3.0,
    )


def _graded_use_cases() -> list[GradedUseCase]:
    return [
        GradedUseCase(
            use_case=_candidate(index),
            score=_score(f"uc_{index}"),
        )
        for index in range(1, 6)
    ]


def _final_selection() -> FinalSelectionOutput:
    return FinalSelectionOutput(selected=_graded_use_cases()[:3])


def test_web_search_system_prompt_includes_current_date() -> None:
    prompt = web_search_system_prompt(date(2026, 4, 25))

    assert "2026-04-25" in prompt
    assert "web search" in prompt
    assert "ANTI-HALLUCINATION RULES" in prompt
    assert "Do not supplement with prior knowledge" in prompt
    assert "Never construct a URL" in prompt
    assert "report that the information was not found" in prompt
    assert "Never ask for confirmation" in prompt


def test_combined_research_prompt_covers_identity_and_research() -> None:
    prompt = combined_research_prompt("Acme")

    assert "Resolve and research this company: Acme" in prompt
    assert "company identity" in prompt
    assert "official company name" in prompt
    assert "ambiguity" in prompt
    assert "immediately proceed to deep research without stopping" in prompt
    assert "Search for recent developments" in prompt
    assert "acquisitions" in prompt
    assert "earnings results" in prompt
    assert "strategic pivots" in prompt
    assert "business lines" in prompt
    assert "named products, platforms" in prompt
    assert "operational pain points" in prompt
    assert "regulatory" in prompt
    assert "Claim:" in prompt
    assert "Source URL:" in prompt
    assert "official company website" in prompt
    assert "annual report" in prompt
    assert "Do not invent facts" in prompt
    assert "Wikipedia only as fallback" in prompt
    assert "CRITICAL: only report facts found in search results" in prompt
    assert "Not found in search results" in prompt
    assert "Never construct a URL" in prompt


def test_company_context_keeps_name_and_research_text() -> None:
    prompt = company_context(_company_profile())

    assert "Company: Acme" in prompt
    assert "Sourced company research text" in prompt
    assert "Acme makes widgets" in prompt
    assert "Source URL: https://example.com/pain-1" in prompt


def test_genai_use_cases_system_prompt_requires_company_anchoring() -> None:
    prompt = genai_use_cases_system_prompt()

    assert "5" in prompt
    assert "ideation_brief" in prompt
    assert "client-workshop-worthy" in prompt
    assert "OBVIOUS IDEAS TO REJECT" in prompt
    assert "first-order" in prompt
    assert "originality test" in prompt
    assert "UNIQUE MOATS" in prompt
    assert "non-obvious" in prompt
    assert "surprise a domain expert" in prompt
    assert "None may overlap with the rejected obvious ideas" in prompt
    assert "unique company moats" in prompt
    assert "recent acquisitions" in prompt
    assert "proprietary platforms" in prompt
    assert "COMPANY ANCHORING" in prompt
    assert "company-specific noun" in prompt
    assert "harder for competitors to replicate" in prompt
    assert "RECENT-NEWS ANCHORING" in prompt
    assert "last 12 months" in prompt
    assert "GENAI MECHANISM DIVERSITY" in prompt
    assert "at least 4 distinct" in prompt
    assert "multimodal" in prompt
    assert "agentic tool-use" in prompt
    assert "DOMAIN DIVERSITY" in prompt
    assert "`business_domain`" in prompt
    assert "at least 3 distinct `business_domain` values" in prompt
    assert "same underlying business process must share the same label" in prompt
    assert "QUALITY GATES" in prompt
    assert "broad chatbot" in prompt
    assert "generic RAG" in prompt
    assert "classical optimization with GenAI branding" in prompt
    assert "'cannot derive'" in prompt
    assert "'cannot handle'" in prompt
    assert "recommendations, decision briefs, explanations" in prompt
    assert "not as optimized parameters" in prompt
    assert "optimized protocols" in prompt
    assert "production optimization" in prompt
    assert "'GenAI is needed'" in prompt
    assert "GenAI adds value by" in prompt
    assert "WORKFLOW DIVERSITY" in prompt
    assert "structurally different GenAI workflow" in prompt
    assert "input modalities" in prompt
    assert "reasoning patterns" in prompt
    assert "output types" in prompt
    assert "workflow shape" in prompt
    assert "data-in-recommendations-out loop" in prompt
    assert "ORIGINALITY TEST" in prompt
    assert "first-order obvious" in prompt
    assert "Do not invent numeric impact" in prompt
    assert "source_backed_metrics" in prompt
    assert "verbatim in the research text" in prompt
    assert "Do not fabricate recent developments" in prompt
    assert "agreed to acquire" in prompt
    assert "grounded_consultant" not in prompt
    assert "moonshot" not in prompt


def test_genai_use_cases_user_prompt_includes_company_json() -> None:
    prompt = genai_use_cases_user_prompt(_company_profile())

    assert "5 `use_cases`" in prompt
    assert "ideation_brief" in prompt
    assert "unique company moats" in prompt
    assert "company-specific noun" in prompt
    assert "harder for competitors to replicate" in prompt
    assert "non-transferability argument" in prompt
    assert "expert judgment" in prompt
    assert '"research_text":' in prompt
    assert "URLs only from that input" in prompt
    assert "use_case_archetype" not in prompt


def test_use_case_grader_prompt_includes_explicit_rubric() -> None:
    prompt = use_case_grader_system_prompt()

    assert "grader_thinking" in prompt
    assert "company_relevance" in prompt
    assert "business_impact" in prompt
    assert "iconicness" in prompt
    assert "genai_fit" in prompt
    assert "feasibility" in prompt
    assert "evidence_strength" in prompt
    assert "1-10" in prompt
    assert "3-5" in prompt
    assert "skeptical" in prompt
    assert "classical" in prompt
    assert "penalties" in prompt
    assert "use_case_id" in prompt
    assert "Do not output weighted_total" in prompt
    assert "Do not rewrite, merge, skip" in prompt
    assert "DimensionRubricLine" in prompt
    assert "Report-worthy test" in prompt
    assert "peer-company template" in prompt
    assert "constrain adjacent scores" in prompt
    assert "NON-TRANSFERABILITY TEST" in prompt
    assert "cap iconicness at 4" in prompt
    assert "average iconicness across a batch of 5" in prompt
    assert "table-stakes GenAI patterns" in prompt
    assert "cap at 5" in prompt
    assert "Compare peer summaries" in prompt
    assert "name the overlapping use_case_id in penalties" in prompt
    assert "adversarial weaknesses" in prompt
    assert "human-reviewable decisions" in prompt


def test_grade_single_use_case_user_prompt_requests_score_only_output() -> None:
    prompt = grade_single_use_case_user_prompt(
        _company_profile(),
        _candidate(1),
        ["uc_2: Use case 2 — Problem"],
    )

    assert "Generated use case to grade (JSON)" in prompt
    assert "Peer use-case summaries for overlap checking only" in prompt
    assert '"id": "uc_1"' in prompt
    assert "uc_2: Use case 2" in prompt
    assert "supplied use_case.id" in prompt
    assert "Do not repeat or rewrite the original use_case object" in prompt
    assert "report-worthy test" in prompt
    assert "read naturally for a peer" in prompt
    assert "keep iconicness low" in prompt
    assert "avoid compensating with high adjacent scores" in prompt
    assert "Name overlapping peer use_case_ids in penalties" in prompt


def test_markdown_reporter_prompt_requires_client_ready_markdown() -> None:
    prompt = markdown_reporter_system_prompt()

    assert "`markdown` field" in prompt
    assert "complete markdown report" in prompt
    assert "Markdown report template" in prompt
    assert MARKDOWN_REPORT_TEMPLATE in prompt
    assert "practical decision memo" in prompt
    assert "generic consulting template" in prompt
    assert "# GenAI Opportunity Report — {Company}" in prompt
    assert "## Company Context" in prompt
    assert "## Recommended Opportunities" in prompt
    assert (
        "| Rank | Opportunity | Primary users | Fit score (/10) | Decision "
        "rationale |" in prompt
    )
    assert "## 1. {Use Case Title}" in prompt
    assert "## 2. {Use Case Title}" in prompt
    assert "## 3. {Use Case Title}" in prompt
    assert "## Limitations" in prompt
    assert "## Sources" in prompt
    assert "score.weighted_total" in prompt
    assert "one-decimal Fit score" in prompt
    assert "7.4/10" in prompt
    assert "not 7.35/10" in prompt
    assert "distinctive" in prompt
    assert "weak iconicness" in prompt
    assert "Scoring (1–10)" in prompt
    assert "How The Workflow Would Work" in prompt
    assert "Retrieved or generated context" in prompt
    assert "Human approval or decision point" in prompt
    assert "why_iconic" in prompt
    assert "weave" in prompt.lower() or "Weave" in prompt
    assert "Do not upgrade a generic use case" in prompt
    assert "reflect low iconicness honestly" in prompt
    assert "DimensionRubricLine" in prompt
    assert "Why GenAI Fits" in prompt
    assert "what GenAI adds" in prompt
    assert "what classical systems should still handle" in prompt
    assert "'cannot derive'" in prompt
    assert "'cannot handle'" in prompt
    assert "recommendations for human review" in prompt
    assert "Never frame them as direct control actions" in prompt
    assert "optimized protocols" in prompt
    assert "production optimization" in prompt
    assert "'GenAI is needed'" in prompt
    assert "GenAI adds value by" in prompt
    assert "Do not editorialize" in prompt
    assert "approximate or omit" in prompt
    assert "genai_mechanism" in prompt
    assert "Impact To Validate" in prompt
    assert "Cite factual claims and numbers" in prompt
    assert "Do not invent facts" in prompt
    assert "agreed to acquire" in prompt
    assert "Do not supplement the evidence brief with general knowledge" in prompt
    assert "Every URL in the report must appear in the evidence brief" in prompt
    assert "source URLs" in prompt
    assert "neutral markdown links like [source](URL)" in prompt
    assert "numeric targets" in prompt
    assert "human-readable validation prose" in prompt
    assert "ideation_brief" in prompt
    assert "grader_thinking" in prompt
    assert "raw JSON" in prompt
    assert "specific data gaps" in prompt
    assert "Do not classify" in prompt
    assert "'are incapable of'" in prompt
    assert "## What To Validate First" not in prompt
    assert "## Caveats and Source Limits" not in prompt
    assert "### Primary and high-confidence sources" not in prompt


def test_markdown_report_evidence_brief_includes_inline_links() -> None:
    brief = markdown_report_evidence_brief(
        _company_profile(),
        _final_selection(),
    )

    assert "Citation-ready evidence brief" in brief
    assert "## Company: Acme" in brief
    assert "## Sourced company research" in brief
    assert "Acme makes widgets" in brief
    assert "Source URL: https://example.com/company" in brief
    assert "## Selected use cases" in brief
    assert "### Rank 1: Use case 1" in brief
    assert "Fit score for report display: 3.0/10" in brief
    assert "Internal weighted score: 3.0/10" in brief
    assert (
        "Pain prominence: Prominence 8 of 10 "
        "[source](https://example.com/source-1)" in brief
    )
    assert "Iconicness (weave into The Opportunity section): Iconic fit" in brief
    assert "Grader rubric (rationale then score" in brief
    assert "Rationale for iconicness. — 3/10" in brief
    assert "Pilot KPIs to validate" in brief
    assert (
        "Manual review cycle time matters because Shows whether the workflow "
        "speeds up expert review." in brief
    )
    assert "Measure it with Compare cycle time before and during the pilot." in brief
    assert "target direction is decrease" in brief
    assert "Evidence source [source](https://example.com/source-1)" in brief
    assert "Company signals: Pain 1, widget_supply" in brief
    assert "Archetype:" not in brief


def test_markdown_reporter_user_prompt_has_brief_and_selection() -> None:
    prompt = markdown_reporter_user_prompt(
        _company_profile(),
        _final_selection(),
    )

    assert "Selected top 3 use cases with scores (JSON" in prompt
    assert "Citation-ready evidence brief" in prompt
    assert "Acme makes widgets" in prompt
    assert "Source URL: https://example.com/company" in prompt
    assert (
        "Pain prominence: Prominence 8 of 10 "
        "[source](https://example.com/source-1)" in prompt
    )
    assert '"id": "uc_1"' in prompt
    assert '"genai_mechanism": {' in prompt
    assert '"document_understanding"' in prompt
    assert '"qualitative_impact": "Qualitative impact"' in prompt
    assert '"source_backed_metrics": [' in prompt
    assert '"pilot_kpis": [' in prompt
    assert '"score": {' in prompt
    assert "Write the final markdown report" in prompt
    assert "evidence brief for citation links" in prompt
    assert "JSON for exact field values" in prompt
    assert "Do not include raw JSON" in prompt
    assert "ideation_brief" in prompt
    assert "grader_thinking" in prompt
