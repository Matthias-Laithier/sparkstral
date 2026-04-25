from datetime import date

from src.prompts import genai_use_cases_system_prompt, web_search_system_prompt


def test_web_search_system_prompt_includes_current_date() -> None:
    prompt = web_search_system_prompt(date(2026, 4, 25))

    assert "2026-04-25" in prompt
    assert "cached_web_search" in prompt


def test_genai_prompt_requires_three_use_cases() -> None:
    prompt = genai_use_cases_system_prompt()

    assert "exactly 3" in prompt
    assert "high-impact" in prompt
