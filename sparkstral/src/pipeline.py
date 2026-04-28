import asyncio
from collections.abc import Awaitable, Callable

from src.activities import (
    fact_check_use_case,
    generate_ideation_brief,
    generate_single_use_case,
    grade_single_use_case,
    research_company,
    select_final_top_3,
    write_markdown_report,
)
from src.agents.grader import (
    build_graded_use_case_pool,
    build_single_use_case_grade_inputs,
)
from src.core.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    FactCheckInput,
    GenAIUseCaseCandidatePool,
    IdeationInput,
    MarkdownReportInput,
    ResearchInput,
    SingleUseCaseInput,
    SparkstralWorkflowResult,
)
from src.utils.fact_check import apply_fact_check

PipelineStatusCallback = Callable[[str], Awaitable[None]]


async def run_sparkstral_pipeline(
    params: CompanyInput,
    status_callback: PipelineStatusCallback,
) -> SparkstralWorkflowResult:
    await status_callback("Researching company context...\n")
    research = await research_company(ResearchInput(company_query=params.company_name))

    company_profile = CompanyProfileOutput(
        company_name=params.company_name,
        research_text=research.text,
    )

    await status_callback("Planning use-case angles...\n")
    ideation = await generate_ideation_brief(
        IdeationInput(company_profile=company_profile)
    )

    await status_callback("Generating candidate use cases...\n")
    single_inputs = [
        SingleUseCaseInput(
            company_profile=company_profile,
            assignment=ideation.assignments[i],
            peer_assignments=[a for j, a in enumerate(ideation.assignments) if j != i],
            use_case_index=i + 1,
        )
        for i in range(5)
    ]
    generated = await asyncio.gather(
        *[generate_single_use_case(inp) for inp in single_inputs]
    )
    raw_use_cases = [g.use_case for g in generated]

    await status_callback("Fact-checking use cases...\n")
    fact_check_inputs = [
        FactCheckInput(company_profile=company_profile, use_case=uc)
        for uc in raw_use_cases
    ]
    fact_checks = await asyncio.gather(
        *[fact_check_use_case(inp) for inp in fact_check_inputs]
    )
    checked_use_cases = [
        apply_fact_check(uc, fc) for uc, fc in zip(raw_use_cases, fact_checks)
    ]
    use_cases = GenAIUseCaseCandidatePool(use_cases=checked_use_cases)

    await status_callback("Scoring opportunities...\n")
    grade_inputs = build_single_use_case_grade_inputs(
        company_profile,
        use_cases.use_cases,
    )
    single_grades = await asyncio.gather(
        *[grade_single_use_case(grade_input) for grade_input in grade_inputs]
    )
    graded_use_cases = build_graded_use_case_pool(use_cases.use_cases, single_grades)

    final_selection = await select_final_top_3(graded_use_cases)

    await status_callback("Writing final report...\n")
    markdown_report = await write_markdown_report(
        MarkdownReportInput(
            company_profile=company_profile,
            final_selection=final_selection,
        )
    )

    return SparkstralWorkflowResult(final=markdown_report.markdown)
