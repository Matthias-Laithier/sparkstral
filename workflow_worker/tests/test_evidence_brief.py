from src.prompts.reporter import narrative_user_prompt

from .factories import make_final_selection, make_profile


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
