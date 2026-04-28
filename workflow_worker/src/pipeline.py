import asyncio
from collections.abc import Awaitable, Callable

from src.activities import (
    generate_genai_use_cases,
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
    GenAIUseCaseCandidateInput,
    GenAIUseCaseCandidatePool,
    MarkdownReportInput,
    ResearchInput,
    SparkstralWorkflowResult,
)

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

    await status_callback("Generating candidate use cases...\n")
    generated = await generate_genai_use_cases(
        GenAIUseCaseCandidateInput(company_profile=company_profile)
    )
    use_cases = GenAIUseCaseCandidatePool(use_cases=generated.use_cases)

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
