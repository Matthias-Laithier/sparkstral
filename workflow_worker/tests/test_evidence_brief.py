from src.prompts.reporter import markdown_report_evidence_brief

from .factories import make_final_selection, make_profile


def test_evidence_brief_renders_scores_links_and_kpis() -> None:
    profile = make_profile()
    selection = make_final_selection()

    brief = markdown_report_evidence_brief(profile, selection)

    assert "## Company: Acme" in brief
    assert "Acme is a manufacturing company." in brief

    for rank in range(1, 4):
        assert f"### Rank {rank}:" in brief

    assert "7.0/10" in brief
    assert "6.0/10" in brief

    assert "[source](https://example.com)" in brief

    assert "KPI A matters because" in brief
    assert "target direction is increase" in brief
    assert "target direction is decrease" in brief

    assert "Company signals: signal_1" in brief
