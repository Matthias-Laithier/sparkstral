import json
from datetime import date

from src.schemas import CompanyProfileOutput, PainPointProfilerOutput


def web_search_system_prompt(today: date) -> str:
    return (
        "You are a research assistant. Use cached_web_search to find accurate, "
        "up-to-date information. Cite the source URL for every fact you report. "
        "Be concise and to the point. "
        f"The current date is {today:%Y-%m-%d}; use it in searches when recency "
        "matters."
    )


def company_research_prompt(company_query: str) -> str:
    return (
        f"Research this company: {company_query}\n\n"
        "Gather: official or common company name; primary industry; 2-5 business "
        "lines; key customers or segments if public; 2-5 strategic priorities; "
        "include the source URL next to each fact.\n"
        "Use few sources: prefer Wikipedia, plus at most one or two other reliable "
        "pages."
    )


def company_resolution_research_prompt(company_query: str) -> str:
    return (
        f"Resolve this company name to the most likely official company: "
        f"{company_query}\n\n"
        "Find the likely official company identity before deeper research. Prefer "
        "the official company website, then reliable sources such as company "
        "registries, annual reports, reputable news, Wikipedia, or Crunchbase. "
        "Explicitly look for ambiguity: similarly named companies, subsidiaries, "
        "brands, regional variants, or common meanings of the name.\n"
        "Gather: official/resolved name; official website; headquarters country; "
        "primary industry; ambiguity notes; and source URLs next to each factual "
        "claim.\n"
        "Use few sources: prefer Wikipedia, plus at most one or two other reliable "
        "pages."
    )


def company_resolution_system_prompt() -> str:
    return (
        "You are a company identity resolution assistant. Given research notes for "
        "an ambiguous company query, resolve the input to the most likely official "
        "company identity.\n"
        "Prefer the official company website and reliable sources. Explicitly "
        "mention ambiguity, including alternative companies or interpretations "
        "when relevant.\n"
        "Only include factual claims supported by the research. Every evidence "
        "item's `source` must be a full URL from the research, not a site name "
        "only."
    )


def company_resolution_user_prompt(company_query: str, research_text: str) -> str:
    return (
        f"Company query: {company_query}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return the resolved company identity. Use `input_name` for the original "
        "query and `resolved_name` for the likely official company name. Include "
        "the official website if available. In `ambiguity_notes`, explain why this "
        "company is the likely match and note credible alternatives. Set "
        "`confidence` from 0.0 to 1.0 based on the evidence strength."
    )


def company_profile_system_prompt() -> str:
    return (
        "You are a data extraction assistant. Given research notes about a company, "
        "extract and return a structured profile.\n"
        "Only include information supported by the research.\n"
        "For every evidence item, `source` must be a full URL (https preferred), "
        "from the research - not a site name only."
    )


def company_profile_user_prompt(company_query: str, research_text: str) -> str:
    return (
        f"Company query: {company_query}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return the structured profile with only the most relevant information. "
        "Be concise: 2-5 items each for business_lines, key_customers, and "
        "strategic_priorities."
    )


def company_context(profile: CompanyProfileOutput) -> str:
    return "Known company profile (from prior step):\n" + json.dumps(
        profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )


def pain_point_research_prompt(profile: CompanyProfileOutput) -> str:
    return (
        "Search the web for major pain points, unmet needs, and structural "
        "challenges in the company's field.\n\n"
        f"{company_context(profile)}\n\n"
        "Use few sources: prefer Wikipedia, plus at most one or two other reliable "
        "pages.\n"
        "Include the full URL for each finding you cite."
    )


def pain_point_system_prompt() -> str:
    return (
        "You are an analyst. Given research notes, extract major pain points, "
        "industry gaps, or unmet needs relevant to the company and its field.\n"
        "Only include points supported by the research. Assign prominence 1-10 "
        "from the evidence strength and business impact. Each pain point's "
        "sources must be full URL strings from the research."
    )


def pain_point_user_prompt(
    profile: CompanyProfileOutput,
    research_text: str,
) -> str:
    return (
        f"{company_context(profile)}\n\n"
        f"Research notes:\n{research_text}\n\n"
        "Return 3-8 pain points. Be specific and avoid duplication."
    )


def genai_use_cases_system_prompt() -> str:
    return (
        "You are a principal GenAI strategy consultant. You receive a structured "
        "company profile and a structured pain-point analysis. Propose exactly 3 "
        "high-impact, company-specific generative-AI use cases that feel iconic "
        "for THIS company, not interchangeable with any other business.\n"
        "Each use case must tie to the company profile, pain points, industry, "
        "and strategic priorities. Be concrete: name workflows, data, org roles, "
        "and what makes the solution distinctive.\n"
        "STRICT: Do not propose overused, generic product ideas, including: "
        "generic customer support chatbot, internal knowledge assistant or RAG "
        "for documents, or generic marketing copy generators, unless the write-up "
        "is so specific to this company that it is clearly not a default listing.\n"
        "Prefer creative combinations of agents, tools, and domain control that "
        "plausibly use this org's data and market position. Vary angles across "
        "the list, such as operations, product, risk, R&D, or partner ecosystem "
        "where relevant."
    )


def genai_use_cases_user_prompt(
    company_profile: CompanyProfileOutput,
    pain_points: PainPointProfilerOutput,
) -> str:
    company_json = json.dumps(
        company_profile.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    pain_json = json.dumps(
        pain_points.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return (
        "Company profile (JSON):\n"
        f"{company_json}\n\n"
        "Pain point analysis (JSON):\n"
        f"{pain_json}\n\n"
        "Output exactly 3 use cases. Each must have: title; target_users (1+); "
        "business_problem; why_this_company; genai_solution; required_data; "
        "expected_impact; risks (1+). Rank them by relevance and impact."
    )
