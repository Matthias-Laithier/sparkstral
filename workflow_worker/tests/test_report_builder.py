from src.core.schemas import ReportNarratives
from src.prompts.reporter import build_report_markdown, narrative_user_prompt

from .factories import make_final_selection, make_profile


def _make_narratives() -> ReportNarratives:
    return ReportNarratives(
        company_context=(
            "Acme reported strong Q1 results. The company operates in manufacturing."
        ),
        opportunity_blurbs=[
            "Use case 1 addresses a key pain point in retail.",
            "Use case 2 leverages the corporate platform.",
            "Use case 3 targets insurance workflows.",
        ],
        decision_rationales=[
            "Leverages unique retail network.",
            "Exploits proprietary corporate data.",
            "Addresses underserved insurance segment.",
        ],
        limitations=[
            "Missing internal cost data for implementation.",
            "Revenue figures from press releases lack breakdowns.",
        ],
    )


def test_build_report_contains_all_sections() -> None:
    profile = make_profile()
    selection = make_final_selection()
    narratives = _make_narratives()

    md = build_report_markdown(profile, selection, narratives)

    assert md.startswith("# GenAI Opportunity Report — Acme")
    assert "## Company Context" in md
    assert "strong Q1 results" in md
    assert "## Recommended Opportunities" in md
    assert "## Limitations" in md
    assert "## Sources" in md


def test_build_report_has_three_use_case_sections() -> None:
    profile = make_profile()
    selection = make_final_selection()
    narratives = _make_narratives()

    md = build_report_markdown(profile, selection, narratives)

    for rank in range(1, 4):
        assert f"## {rank}." in md
        assert "### The Opportunity" in md
        assert "### Scoring (1–10)" in md
        assert "### Why GenAI Fits" in md
        assert "### Data and Integration Needs" in md
        assert "### Impact To Validate" in md
        assert "### Risks and Mitigations" in md


def test_build_report_summary_table_has_scores() -> None:
    profile = make_profile()
    selection = make_final_selection()
    narratives = _make_narratives()

    md = build_report_markdown(profile, selection, narratives)

    assert "7.0/10" in md
    assert "6.0/10" in md
    assert "5.0/10" in md
    assert "Leverages unique retail network." in md
    assert "25% iconicness" in md


def test_build_report_sources_deduplicates() -> None:
    profile = make_profile()
    selection = make_final_selection()
    narratives = _make_narratives()

    md = build_report_markdown(profile, selection, narratives)

    sources_section = md.split("## Sources")[-1]
    assert sources_section.count("[https://example.com](https://example.com)") == 1


def test_narrative_prompt_renders_key_sections() -> None:
    profile = make_profile()
    selection = make_final_selection()

    prompt = narrative_user_prompt(profile, selection)

    assert "## Company: Acme" in prompt
    assert "Acme is a manufacturing company." in prompt

    for rank in range(1, 4):
        assert f"### Rank {rank}:" in prompt

    assert "7.0/10" in prompt
    assert "6.0/10" in prompt

    assert "[source](https://example.com)" in prompt
