from datetime import date

from src.prompts import (
    MARKDOWN_REPORT_TEMPLATE,
    company_profile_system_prompt,
    company_profile_user_prompt,
    company_research_prompt,
    genai_use_cases_system_prompt,
    genai_use_cases_user_prompt,
    markdown_report_evidence_brief,
    markdown_reporter_system_prompt,
    markdown_reporter_user_prompt,
    pain_point_system_prompt,
    pain_point_user_prompt,
    use_case_deduplicator_system_prompt,
    use_case_deduplicator_user_prompt,
    use_case_grader_system_prompt,
    use_case_grader_user_prompt,
    web_search_system_prompt,
)
from src.schemas import (
    CompanyEvidenceClaim,
    CompanyProfileOutput,
    CompanyResolutionOutput,
    EvidenceItem,
    FinalSelectionOutput,
    GenAIMechanism,
    GenAIUseCaseCandidate,
    GradedUseCase,
    PainPointItem,
    PainPointProfilerOutput,
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
        why_classical_software_is_not_enough=(
            "Rules alone cannot synthesize messy operational context."
        ),
        why_classical_ml_or_optimization_is_not_enough=(
            "A predictor or optimizer would not draft grounded recommendations."
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
        id=f"uc-{index}",
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
        linked_pain_points=["Pain 1"],
        evidence_sources=[evidence_source],
        ideation_lens="grounded consultant",
    )


def _company_claim(
    claim: str,
    source_url: str,
    citation: str,
) -> CompanyEvidenceClaim:
    return CompanyEvidenceClaim(
        claim=claim,
        source_url=source_url,
        citation=citation,
    )


def _company_claims() -> list[CompanyEvidenceClaim]:
    return [
        _company_claim(
            "Acme makes widgets",
            "https://example.com/company",
            "Company page describes widget products.",
        ),
        _company_claim(
            "Acme serves industrial buyers",
            "https://example.com/customers",
            "Customer page names industrial buyers.",
        ),
        _company_claim(
            "Acme prioritizes operational efficiency",
            "https://example.com/strategy",
            "Strategy page lists operational efficiency.",
        ),
        _company_claim(
            "Acme launched a factory modernization initiative",
            "https://example.com/initiative",
            "Press release announces modernization.",
        ),
        _company_claim(
            "Acme operates in North America",
            "https://example.com/markets",
            "Markets page lists North America.",
        ),
        _company_claim(
            "Acme faces supply chain delays",
            "https://example.com/pain-1",
            "Annual report notes supply chain delays.",
        ),
        _company_claim(
            "New safety rules affect Acme's plants",
            "https://example.com/pain-2",
            "Regulator page describes new safety rules.",
        ),
        _company_claim(
            "Customers expect faster configuration support",
            "https://example.com/pain-3",
            "Publication reports faster configuration expectations.",
        ),
        _company_claim(
            "Acme has an aftermarket service expansion opportunity",
            "https://example.com/growth",
            "Investor presentation highlights aftermarket service expansion.",
        ),
        _company_claim(
            "Acme is modernizing factory systems",
            "https://example.com/digital",
            "Digital page describes factory system modernization.",
        ),
        _company_claim(
            "Acme tracks on-time delivery as a customer metric",
            "https://example.com/metrics",
            "Annual report references on-time delivery.",
        ),
        _company_claim(
            "Acme sells through distributor partners",
            "https://example.com/partners",
            "Partner page describes distributor channels.",
        ),
        _company_claim(
            "Acme focuses on configurable industrial products",
            "https://example.com/configurable-products",
            "Products page describes configurable industrial products.",
        ),
        _company_claim(
            "Acme is investing in quality management",
            "https://example.com/quality",
            "Strategy update describes quality management investment.",
        ),
        _company_claim(
            "Acme Corporation is the official company name",
            "https://example.com/about",
            "About page uses Acme Corporation as the official name.",
        ),
    ]


def _company_profile() -> CompanyProfileOutput:
    return CompanyProfileOutput(
        company_name="Acme Corporation",
        industry="Manufacturing",
        business_lines=["Widgets"],
        key_customers=["Industrial buyers"],
        customer_segments=["Industrial buyers"],
        strategic_priorities=["Operational efficiency"],
        recent_strategic_initiatives=["Factory modernization"],
        geography_markets=["North America"],
        operational_context=["Supply chain delays"],
        regulatory_context=["New safety rules"],
        customer_market_pressure=["Customers expect faster configuration support"],
        growth_opportunities=["Aftermarket service expansion"],
        technology_transformation_context=["Factory modernization"],
        claims=_company_claims(),
    )


def _pain_point(index: int) -> PainPointItem:
    return PainPointItem(
        title=f"Pain {index}",
        description="Description",
        prominence=8,
        sources=[f"https://example.com/pain-{index}"],
    )


def _pain_points() -> PainPointProfilerOutput:
    return PainPointProfilerOutput(
        pain_points=[_pain_point(1), _pain_point(2), _pain_point(3)]
    )


def _score(use_case_id: str) -> UseCaseScore:
    return UseCaseScore(
        use_case_id=use_case_id,
        strengths=["Strength"],
        weaknesses=["Weakness"],
        rationale="Rationale",
        company_relevance=3,
        business_impact=3,
        iconicness=3,
        genai_fit=3,
        feasibility=3,
        evidence_strength=3,
        penalties=[],
        weighted_total=3.0,
    )


def _graded_use_cases() -> list[GradedUseCase]:
    return [
        GradedUseCase(
            use_case=_candidate(index),
            score=_score(f"uc-{index}"),
        )
        for index in range(1, 6)
    ]


def _final_selection() -> FinalSelectionOutput:
    return FinalSelectionOutput(selected=_graded_use_cases()[:3])


def _assert_high_quality_source_guidance(prompt: str) -> None:
    assert "Claim:" in prompt
    assert "Source URL:" in prompt
    assert "Citation:" in prompt
    assert "official company sources" in prompt
    assert "annual reports" in prompt
    assert "reputable industry sources" in prompt
    assert "Use Wikipedia only as basic-identity fallback" in prompt
    assert "Do not invent facts" in prompt
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
    assert "do not redo basic identity discovery" in prompt
    assert "Reuse useful resolution URLs" in prompt
    assert "business lines" in prompt
    assert "key customers" in prompt
    assert "customer segments" in prompt
    assert "strategic priorities" in prompt
    assert "recent initiatives" in prompt
    assert "geography/markets" in prompt
    assert "operational pain points" in prompt
    assert "regulatory pressure" in prompt
    assert "customer/market pressure" in prompt
    assert "growth opportunities" in prompt
    assert "technology transformation context" in prompt
    assert "Omit facts without full source URLs" in prompt
    assert "mark material uncertainty" in prompt
    _assert_high_quality_source_guidance(prompt)


def test_company_profile_prompts_request_enriched_evidence_contract() -> None:
    system_prompt = company_profile_system_prompt()
    user_prompt = company_profile_user_prompt("Acme Corporation", "Research notes")

    assert "compact company profile" in system_prompt
    assert "`claims` as the evidence ledger" in system_prompt
    assert "full source_url" in system_prompt
    assert "customer_segments" in user_prompt
    assert "recent_strategic_initiatives" in user_prompt
    assert "geography_markets" in user_prompt
    assert "operational_context" in user_prompt
    assert "regulatory_context" in user_prompt
    assert "customer_market_pressure" in user_prompt
    assert "growth_opportunities" in user_prompt
    assert "technology_transformation_context" in user_prompt
    assert "at least 15 claims" in user_prompt
    assert "source_url, and citation" in user_prompt
    assert "Copy source_url exactly from the research text" in user_prompt
    assert "Drop facts without full URLs or citations" in user_prompt
    assert "Do not invent missing facts" in user_prompt


def test_pain_point_prompts_derive_from_enriched_profile_evidence() -> None:
    system_prompt = pain_point_system_prompt()
    user_prompt = pain_point_user_prompt(_company_profile())

    assert "company_profile.claims" in system_prompt
    assert "copy source URLs from those claims" in system_prompt
    assert "do not add web research" in system_prompt
    assert "unsupported industry generalizations" in system_prompt
    assert "Acme Corporation" in user_prompt
    assert "operational_context" in user_prompt
    assert "regulatory_context" in user_prompt
    assert "customer_market_pressure" in user_prompt
    assert "growth_opportunities" in user_prompt
    assert "technology_transformation_context" in user_prompt
    assert "Assign prominence 1-10" in user_prompt
    assert "copy each source URL from company_profile.claims" in user_prompt


def test_genai_prompt_requires_persona_batch() -> None:
    prompt = genai_use_cases_system_prompt("moonshot strategist", "moonshot_uc")

    assert "exactly 3" in prompt
    assert "moonshot strategist" in prompt
    assert "moonshot_uc_1" in prompt
    assert "moonshot_uc_2" in prompt
    assert "moonshot_uc_3" in prompt
    assert "GenAI-native" in prompt
    assert "ordinary software or classical ML" in prompt
    assert "internal knowledge assistant or RAG" in prompt
    assert "generic customer support chatbot" in prompt
    assert "Do not invent numeric impact" in prompt
    assert "source_backed_metrics" in prompt
    assert "pilot_kpis" in prompt
    assert "company_profile.claims" in prompt
    assert "meaningfully varied" in prompt
    assert "why_iconic" in prompt


def test_genai_user_prompt_requires_mechanism_and_workflow() -> None:
    prompt = genai_use_cases_user_prompt(
        _company_profile(),
        _pain_points(),
        "why not? inventor",
        "why_not_uc",
    )

    assert "exactly 3" in prompt
    assert "why not? inventor" in prompt
    assert "why_not_uc_1" in prompt
    assert "why_not_uc_2" in prompt
    assert "why_not_uc_3" in prompt
    assert "genai_mechanism" in prompt
    assert "mechanisms (1+)" in prompt
    assert "three why_* fields" in prompt
    assert "who uses it" in prompt
    assert "what they input" in prompt
    assert "what the system generates" in prompt
    assert "human approval step" in prompt
    assert "qualitative_impact" in prompt
    assert "source_backed_metrics" in prompt
    assert "pilot_kpis (2+)" in prompt
    assert "do not invent target values" in prompt
    assert "company_profile.claims" in prompt
    assert '"claims": [' in prompt


def test_use_case_deduplicator_prompt_only_allows_retained_ids() -> None:
    prompt = use_case_deduplicator_system_prompt()

    assert "retained_use_case_ids" in prompt
    assert "Do not rewrite" in prompt
    assert "merge" in prompt
    assert "create use cases" in prompt
    assert "Retain at least 5" in prompt
    assert "Shared pain points" in prompt


def test_use_case_deduplicator_user_prompt_includes_original_use_cases() -> None:
    prompt = use_case_deduplicator_user_prompt(
        _company_profile(),
        _pain_points(),
        [_candidate(1), _candidate(2), _candidate(3), _candidate(4), _candidate(5)],
    )

    assert "Generated use cases to deduplicate (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert "Available use_case IDs: uc-1, uc-2, uc-3, uc-4, uc-5" in prompt
    assert "Return retained_use_case_ids only" in prompt
    assert "Retain at least 5 use cases" in prompt
    assert "Do not output rewritten use cases" in prompt
    assert "merged use cases" in prompt
    assert "changed fields" in prompt


def test_use_case_grader_prompt_includes_explicit_rubric() -> None:
    prompt = use_case_grader_system_prompt()

    assert "company_relevance" in prompt
    assert "business_impact" in prompt
    assert "iconicness" in prompt
    assert "genai_fit" in prompt
    assert "feasibility" in prompt
    assert "evidence_strength" in prompt
    assert "full 1-10 scale" in prompt
    assert "ordinary ideas 4-6" in prompt
    assert "rare exceptional ideas 9-10" in prompt
    assert "iconicness (main differentiator)" in prompt
    assert "generic chatbots" in prompt
    assert "classical ML/optimization" in prompt
    assert "unsupported metrics" in prompt
    assert "vague users" in prompt
    assert "penalties" in prompt
    assert "use_case_id" in prompt
    assert "Do not output weighted_total" in prompt
    assert "Do not skip" in prompt


def test_use_case_grader_user_prompt_requests_score_only_output() -> None:
    prompt = use_case_grader_user_prompt(
        _company_profile(),
        _pain_points(),
        [_candidate(1), _candidate(2)],
    )

    assert "Generated use cases to grade (JSON)" in prompt
    assert '"id": "uc-1"' in prompt
    assert "Return one grades item for every use case above" in prompt
    assert "use_case_id equal to the matching use_case.id" in prompt
    assert "Do not repeat, copy, or rewrite any original use_case object" in prompt
    assert "1-10 scale" in prompt
    assert "company_relevance as a grounding check" in prompt
    assert "iconicness as the main differentiator" in prompt
    assert "Return one graded_use_cases item" not in prompt
    assert "Keep each original use_case object unchanged" not in prompt


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
    assert "## Ranked Opportunities" in prompt
    assert (
        "| Rank | Opportunity | Primary users | Weighted score | Decision rationale |"
        in prompt
    )
    assert "## 1. {Use Case Title}" in prompt
    assert "## 2. {Use Case Title}" in prompt
    assert "## 3. {Use Case Title}" in prompt
    assert "## What To Validate First" in prompt
    assert "## Caveats and Source Limits" in prompt
    assert "## Sources" in prompt
    assert "score.weighted_total" in prompt
    assert "How The Workflow Would Work" in prompt
    assert "Retrieved or generated context" in prompt
    assert "Human approval or decision point" in prompt
    assert "Iconicness" in prompt
    assert "why_iconic" in prompt
    assert "score.iconicness" in prompt
    assert "Why Genai ?" in prompt
    assert "Why GenAI Is Needed" not in prompt
    assert "genai_mechanism" in prompt
    assert "Impact To Validate" in prompt
    assert "Cite factual claims and numbers" in prompt
    assert "Do not invent facts" in prompt
    assert "source URLs" in prompt
    assert "numeric targets" in prompt
    assert "human-readable validation prose" in prompt
    assert "What To Validate First" in prompt


def test_markdown_report_evidence_brief_includes_inline_links() -> None:
    brief = markdown_report_evidence_brief(
        _company_profile(),
        _pain_points(),
        _final_selection(),
    )

    assert "Citation-ready evidence brief" in brief
    assert "## Company claims" in brief
    assert "Acme makes widgets [source](https://example.com/company)" in brief
    assert "## Pain points" in brief
    assert (
        "Pain 1: Description (prominence 8/10) "
        "[source](https://example.com/pain-1)" in brief
    )
    assert "## Selected use cases" in brief
    assert "### Rank 1: Use case 1" in brief
    assert "Weighted score: 3.0" in brief
    assert (
        "Pain prominence: Prominence 8 of 10 "
        "[source](https://example.com/source-1)" in brief
    )
    assert "Iconicness: Iconic fit (score 3/10; rationale: Rationale)" in brief
    assert "Pilot KPIs to validate" in brief
    assert (
        "Manual review cycle time matters because Shows whether the workflow "
        "speeds up expert review." in brief
    )
    assert "Measure it with Compare cycle time before and during the pilot." in brief
    assert "target direction is decrease" in brief
    assert "Evidence source [source](https://example.com/source-1)" in brief


def test_markdown_reporter_user_prompt_includes_direct_input_json() -> None:
    prompt = markdown_reporter_user_prompt(
        _company_profile(),
        _pain_points(),
        _final_selection(),
    )

    assert "Company profile (JSON)" in prompt
    assert "Pain point analysis (JSON)" in prompt
    assert "Selected top 3 use cases with scores (JSON)" in prompt
    assert "Citation-ready evidence brief" in prompt
    assert "Acme makes widgets [source](https://example.com/company)" in prompt
    assert (
        "Pain 1: Description (prominence 8/10) "
        "[source](https://example.com/pain-1)" in prompt
    )
    assert (
        "Pain prominence: Prominence 8 of 10 "
        "[source](https://example.com/source-1)" in prompt
    )
    assert '"company_name": "Acme Corporation"' in prompt
    assert '"id": "uc-1"' in prompt
    assert '"genai_mechanism": {' in prompt
    assert '"document_understanding"' in prompt
    assert '"qualitative_impact": "Qualitative impact"' in prompt
    assert '"claims": [' in prompt
    assert '"source_url": "https://example.com/pain-1"' in prompt
    assert '"source_backed_metrics": [' in prompt
    assert '"pilot_kpis": [' in prompt
    assert '"score": {' in prompt
    assert "Write the final markdown report" in prompt
    assert "evidence brief for citation links" in prompt
    assert "JSON as source of truth" in prompt
    assert "Do not include raw JSON" in prompt
