from src.core.schemas import (
    FactCheckOutput,
    NarrativeFactCheckInput,
    NarrativeFactCheckOutput,
)
from src.prompts.fact_check import (
    fact_check_narratives_system_prompt,
    fact_check_narratives_user_prompt,
    fact_check_system_prompt,
    fact_check_user_prompt,
)
from src.utils.fact_check import apply_fact_check

from .factories import make_candidate, make_narratives, make_profile


def test_apply_fact_check_patches_text_fields() -> None:
    original = make_candidate(1)
    corrected = FactCheckOutput(
        business_problem="Corrected problem",
        genai_solution="Corrected solution",
        why_this_company="Corrected fit",
        why_iconic="Corrected iconic",
        feasibility_notes="Corrected feasibility",
        required_data=["New data source"],
        corrections_planned=["Removed invented statistic"],
    )

    result = apply_fact_check(original, corrected)

    assert result.business_problem == "Corrected problem"
    assert result.genai_solution == "Corrected solution"
    assert result.why_this_company == "Corrected fit"
    assert result.why_iconic == "Corrected iconic"
    assert result.feasibility_notes == "Corrected feasibility"
    assert result.required_data == ["New data source"]


def test_apply_fact_check_preserves_structured_fields() -> None:
    original = make_candidate(1)
    corrected = FactCheckOutput(
        business_problem="Changed",
        genai_solution="Changed",
        why_this_company="Changed",
        why_iconic="Changed",
        feasibility_notes="Changed",
        required_data=["Changed"],
        corrections_planned=["something"],
    )

    result = apply_fact_check(original, corrected)

    assert result.id == original.id
    assert result.title == original.title
    assert result.business_domain == original.business_domain
    assert result.target_users == original.target_users
    assert result.genai_mechanism == original.genai_mechanism
    assert result.pilot_kpis == original.pilot_kpis
    assert result.risks == original.risks
    assert result.evidence_sources == original.evidence_sources
    assert result.source_backed_metrics == original.source_backed_metrics


def test_apply_fact_check_identity() -> None:
    """When the fact-checker changes nothing, the result equals the original."""
    original = make_candidate(1)
    identity = FactCheckOutput(
        business_problem=original.business_problem,
        genai_solution=original.genai_solution,
        why_this_company=original.why_this_company,
        why_iconic=original.why_iconic,
        feasibility_notes=original.feasibility_notes,
        required_data=list(original.required_data),
        corrections_planned=[],
    )

    result = apply_fact_check(original, identity)

    assert result == original


def test_fact_check_system_prompt_mentions_grounding() -> None:
    prompt = fact_check_system_prompt()
    assert "fact-checker" in prompt.lower()
    assert "research" in prompt.lower()


def test_fact_check_system_prompt_mentions_product_names() -> None:
    prompt = fact_check_system_prompt()
    assert "product name" in prompt.lower()


def test_fact_check_user_prompt_includes_research_and_use_case() -> None:
    profile = make_profile()
    candidate = make_candidate(1)
    prompt = fact_check_user_prompt(profile, candidate)

    assert profile.research_text in prompt
    assert candidate.id in prompt


# ---------------------------------------------------------------------------
# Narrative fact-check tests
# ---------------------------------------------------------------------------


def test_narrative_fact_check_input_accepts_valid_data() -> None:
    profile = make_profile()
    narratives = make_narratives()
    inp = NarrativeFactCheckInput(company_profile=profile, narratives=narratives)
    assert inp.company_profile.company_name == "Acme"
    assert len(inp.narratives.opportunity_blurbs) == 3


def test_narrative_fact_check_output_schema() -> None:
    out = NarrativeFactCheckOutput(
        company_context="Fixed context.",
        opportunity_blurbs=["a", "b", "c"],
        corrections_planned=["Fixed date"],
    )
    assert out.corrections_planned == ["Fixed date"]


def test_narrative_fact_check_output_empty_corrections() -> None:
    out = NarrativeFactCheckOutput(
        company_context="Same.",
        opportunity_blurbs=["a", "b", "c"],
        corrections_planned=[],
    )
    assert out.corrections_planned == []


def test_fact_check_narratives_system_prompt_content() -> None:
    prompt = fact_check_narratives_system_prompt()
    assert "fact-checker" in prompt.lower()
    assert "research" in prompt.lower()
    assert "discontinued" in prompt.lower()


def test_fact_check_narratives_user_prompt_includes_research_and_narratives() -> None:
    profile = make_profile()
    narratives = make_narratives()
    prompt = fact_check_narratives_user_prompt(profile, narratives)

    assert profile.research_text in prompt
    assert narratives.company_context in prompt
    for blurb in narratives.opportunity_blurbs:
        assert blurb in prompt
