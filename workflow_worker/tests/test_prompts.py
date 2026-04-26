from datetime import date

from src.prompts import (
    MARKDOWN_REPORT_TEMPLATE,
    company_context,
    company_research_prompt,
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
    CompanyResolutionOutput,
    DimensionRubricLine,
    EvidenceItem,
    FinalSelectionOutput,
    GenAIMechanism,
    GenAIUseCaseCandidate,
    GradedUseCase,
    PilotKPI,
    SourceBackedMetric,
    UseCaseScore,
)


def _company_resolution() -> CompanyResolutionOutput:
    return CompanyResolutionOutput(
        input_name="Acme",
        resolved_name="Acme Corporation",
        website="https://example.com",
        headquarters_country="United States",
        primary_industry="Manufacturing",
        ambiguity_notes="Acme Corporation is the likely match.",
        confidence=0.9,
        evidence=[
            EvidenceItem(
                claim="Acme Corporation is a manufacturing company",
                source="https://example.com/company",
            )
        ],
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
        use_case_archetype="grounded_consultant",
    )


def _company_profile() -> CompanyProfileOutput:
    return CompanyProfileOutput(
        company_resolution=_company_resolution(),
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


def _assert_high_quality_source_guidance(prompt: str) -> None:
    assert "Claim:" in prompt
    assert "Source URL:" in prompt
    assert "Citation:" in prompt
    assert "Source role:" in prompt
    assert "Support directness:" in prompt
    assert "`company_primary`" in prompt
    assert "`filing_or_investor`" in prompt
    assert "`official_press_release`" in prompt
    assert "`regulator_or_government`" in prompt
    assert "`wire_or_business_media`" in prompt
    assert "`background_only`" in prompt
    assert "`uncertain`" in prompt
    assert "`direct`" in prompt
    assert "`partial`" in prompt
    assert "`background`" in prompt
    assert "official company website" in prompt
    assert "annual report" in prompt
    assert "reputable business or industry publication" in prompt
    assert "Wikipedia only as fallback" in prompt
    assert "Do not invent facts" in prompt
    assert "Do not use hardcoded domain reputation" in prompt
    assert "allowlists, or blocklists" in prompt
    assert "prefer Wikipedia" not in prompt


def test_web_search_system_prompt_includes_current_date() -> None:
    prompt = web_search_system_prompt(date(2026, 4, 25))

    assert "2026-04-25" in prompt
    assert "web search" in prompt


def test_company_research_prompt_prioritizes_high_quality_sources() -> None:
    prompt = company_research_prompt(_company_resolution())

    assert "Research this resolved company comprehensively: Acme Corporation" in prompt
    assert "Structured company resolution from the previous step" in prompt
    assert '"resolved_name": "Acme Corporation"' in prompt
    assert '"website": "https://example.com"' in prompt
    assert '"ambiguity_notes": "Acme Corporation is the likely match."' in prompt
    assert '"source": "https://example.com/company"' in prompt
    assert "Do not spend the research repeating basic identity discovery" in prompt
    assert "Preserve and reuse useful URLs" in prompt
    assert "business lines" in prompt
    assert "key customers" in prompt
    assert "customer segments" in prompt
    assert "strategic priorities" in prompt
    assert "recent strategic initiatives" in prompt
    assert "geography/markets" in prompt
    assert "operational pain points" in prompt
    assert "regulatory pressure" in prompt
    assert "customer/market pressure" in prompt
    assert "growth opportunities" in prompt
    assert "technology/digital transformation context" in prompt
    assert "Omit claims that do not have a full source URL" in prompt
    assert "Clearly mark uncertainty" in prompt
    _assert_high_quality_source_guidance(prompt)


def test_company_context_keeps_resolution_and_research_text() -> None:
    prompt = company_context(_company_profile())

    assert "Resolved company identity (JSON)" in prompt
    assert '"resolved_name": "Acme Corporation"' in prompt
    assert '"source": "https://example.com/company"' in prompt
    assert "Sourced company research text" in prompt
    assert "Acme makes widgets" in prompt
    assert "Source URL: https://example.com/pain-1" in prompt


def test_genai_use_cases_system_prompt_requires_diverse_batch() -> None:
    prompt = genai_use_cases_system_prompt()

    assert "6-10" in prompt or "6–10" in prompt
    assert "ideation_brief" in prompt
    assert "client-workshop-worthy" in prompt
    assert "what you rejected as too generic" in prompt
    assert "reusable anchor types" in prompt
    assert "Do not steer toward any preselected idea" in prompt
    assert "Discard candidates" in prompt
    assert "below 7/10 on iconicness" in prompt
    assert "peer-company template" in prompt
    assert "'digital transformation'" in prompt
    assert "broad chatbot" in prompt
    assert "generic RAG" in prompt
    assert "classical optimization with GenAI branding" in prompt
    assert "agentic tool use" in prompt
    assert "document or multimodal understanding" in prompt
    assert "grounded RAG" in prompt
    assert "long-context or multi-document" in prompt
    assert "grounded_consultant" in prompt
    assert "optimistic_stretch" in prompt
    assert "moonshot" in prompt
    assert "novel_surprise" in prompt
    assert "evidence_tight" in prompt
    assert (
        "No two use cases may share the same users, problem, and core GenAI "
        "workflow" in prompt
    )
    assert "classical software or ML should still handle" in prompt
    assert "Do not invent numeric impact" in prompt
    assert "source_backed_metrics" in prompt
    assert "why_iconic" in prompt


def test_genai_use_cases_user_prompt_includes_company_json() -> None:
    prompt = genai_use_cases_user_prompt(_company_profile())

    assert "6-10 `use_cases`" in prompt
    assert "ideation_brief" in prompt
    assert "use_cases" in prompt
    assert "company_signal_labels" in prompt
    assert "use_case_archetype" in prompt
    assert "genai_mechanism" in prompt
    assert "genai_advantage_over_classical_software" in prompt
    assert "genai_advantage_over_classical_ml" in prompt
    assert "modalities" in prompt
    assert "model+tool loop" in prompt
    assert "human approval" in prompt
    assert '"research_text":' in prompt
    assert "Candidate inclusion test" in prompt
    assert "title names a company anchor" in prompt
    assert "non-transferability argument" in prompt
    assert "expert judgment" in prompt
    assert "URLs only from those inputs" in prompt


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
    assert "cap iconicness at 5" in prompt
    assert "Report-worthy test" in prompt
    assert "peer-company template" in prompt
    assert "constrain adjacent scores" in prompt
    assert "generic value" in prompt
    assert "classical automation in disguise" in prompt
    assert "weak anchors" in prompt
    assert "thin chatbot" in prompt
    assert "human-reviewable decisions" in prompt
    assert "Compare peer summaries" in prompt
    assert "name the overlapping use_case_id in penalties" in prompt
    assert "adversarial weaknesses" in prompt


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
    assert "Pain point and opportunity analysis" not in prompt


def test_markdown_reporter_prompt_requires_client_ready_markdown() -> None:
    prompt = markdown_reporter_system_prompt()

    assert "`markdown` field" in prompt
    assert "complete markdown report" in prompt
    assert "Markdown report template" in prompt
    assert MARKDOWN_REPORT_TEMPLATE in prompt
    assert "practical decision memo" in prompt
    assert "generic consulting template" in prompt
    assert "# GenAI Opportunity Report — {Company}" in prompt
    assert "## Recommendation in Brief" not in prompt
    assert "## What We Know About the Company" in prompt
    assert "## Strategic signals from research" not in prompt
    assert "## Ranked Opportunities" in prompt
    assert (
        "| Rank | Opportunity | Primary users | Fit score (/10) | Decision "
        "rationale |" in prompt
    )
    assert "## 1. {Use Case Title}" in prompt
    assert "## 2. {Use Case Title}" in prompt
    assert "## 3. {Use Case Title}" in prompt
    assert "## What To Validate First" in prompt
    assert "## Caveats and Source Limits" in prompt
    assert "## Sources" in prompt
    assert "score.weighted_total" in prompt
    assert "one-decimal Fit score" in prompt
    assert "7.4/10" in prompt
    assert "not 7.35/10" in prompt
    assert "/10" in prompt
    assert "distinctive" in prompt
    assert "weak iconicness" in prompt
    assert "Scoring (1–10)" in prompt
    assert "How The Workflow Would Work" in prompt
    assert "Retrieved or generated context" in prompt
    assert "Human approval or decision point" in prompt
    assert "Iconicness" in prompt
    assert "why_iconic" in prompt
    assert "Do not upgrade a generic use case" in prompt
    assert "reflect low iconicness honestly" in prompt
    assert "DimensionRubricLine" in prompt
    assert "Why GenAI Fits" in prompt
    assert "Why Genai ?" not in prompt
    assert "Why GenAI Is Needed" not in prompt
    assert "what GenAI adds" in prompt
    assert "what classical systems should still handle" in prompt
    assert "Avoid absolute claims" in prompt
    assert "genai_mechanism" in prompt
    assert "Impact To Validate" in prompt
    assert "Cite factual claims and numbers" in prompt
    assert "Do not invent facts" in prompt
    assert "source URLs" in prompt
    assert "neutral markdown links like [source](URL)" in prompt
    assert "Caveats and Source Limits" in prompt
    assert "numeric targets" in prompt
    assert "human-readable validation prose" in prompt
    assert "ideation_brief" in prompt
    assert "grader_thinking" in prompt
    assert "raw JSON" in prompt
    assert "What To Validate First" in prompt
    assert "'classical software cannot handle X'" in prompt
    assert "domain allowlists, blocklists, regexes" in prompt


def test_markdown_report_evidence_brief_includes_inline_links() -> None:
    brief = markdown_report_evidence_brief(
        _company_profile(),
        _final_selection(),
    )

    assert "Citation-ready evidence brief" in brief
    assert "## Resolved company identity" in brief
    assert "Acme Corporation is a manufacturing company" in brief
    assert "## Sourced company research" in brief
    assert "Acme makes widgets" in brief
    assert "Source URL: https://example.com/company" in brief
    assert "## Pain points" not in brief
    assert "## Selected use cases" in brief
    assert "### Rank 1: Use case 1" in brief
    assert "Fit score for report display: 3.0/10" in brief
    assert "Internal weighted score: 3.0/10" in brief
    assert (
        "Pain prominence: Prominence 8 of 10 "
        "[source](https://example.com/source-1)" in brief
    )
    assert "Iconicness (narrative for the report's Iconicness section): Iconic fit" in (
        brief
    )
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
    assert "Archetype: grounded_consultant" in brief


def test_markdown_reporter_user_prompt_includes_direct_input_json() -> None:
    prompt = markdown_reporter_user_prompt(
        _company_profile(),
        _final_selection(),
    )

    assert "Company profile (resolved identity + sourced research JSON)" in prompt
    assert "Selected top 3 use cases with scores (JSON)" in prompt
    assert "Citation-ready evidence brief" in prompt
    assert "Acme makes widgets" in prompt
    assert "Source URL: https://example.com/company" in prompt
    assert (
        "Pain prominence: Prominence 8 of 10 "
        "[source](https://example.com/source-1)" in prompt
    )
    assert '"resolved_name": "Acme Corporation"' in prompt
    assert '"id": "uc_1"' in prompt
    assert '"genai_mechanism": {' in prompt
    assert '"document_understanding"' in prompt
    assert '"qualitative_impact": "Qualitative impact"' in prompt
    assert '"research_text":' in prompt
    assert '"source_backed_metrics": [' in prompt
    assert '"pilot_kpis": [' in prompt
    assert '"score": {' in prompt
    assert "Write the final markdown report" in prompt
    assert "evidence brief for citation links" in prompt
    assert "JSON as source of truth" in prompt
    assert "Do not include raw JSON" in prompt
    assert "ideation_brief" in prompt
    assert "grader_thinking" in prompt
    assert "Pain point and opportunity analysis" not in prompt
