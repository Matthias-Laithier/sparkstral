from collections.abc import Awaitable, Callable
from functools import partial

from src.activities import (
    generate_genai_use_cases,
    grade_use_cases,
    research_company,
    research_company_resolution,
    select_final_top_3,
    structure_company_resolution,
    write_markdown_report,
)
from src.schemas import (
    CompanyInput,
    CompanyProfileOutput,
    CompanyResolutionInput,
    CompanyResolutionStructuringInput,
    GenAIUseCaseCandidateInput,
    GenAIUseCaseCandidatePool,
    GradeUseCasesInput,
    MarkdownReportInput,
    PipelineOutput,
    SparkstralWorkflowResult,
)
from src.utils import append_json_output, append_text_output

PipelineStatusCallback = Callable[[str], Awaitable[None]]


async def _send_status(
    status_callback: PipelineStatusCallback | None,
    message: str,
) -> None:
    if status_callback is not None:
        await status_callback(message)


async def run_sparkstral_pipeline(
    params: CompanyInput,
    status_callback: PipelineStatusCallback | None = None,
) -> SparkstralWorkflowResult:
    outputs: list[PipelineOutput] = []
    append_text = partial(append_text_output, outputs)
    append_json = partial(append_json_output, outputs)

    await _send_status(status_callback, "Researching company context...\n")
    resolution_research = await research_company_resolution(
        CompanyResolutionInput(company_query=params.company_name)
    )
    append_text(resolution_research.text)

    company_resolution = await structure_company_resolution(
        CompanyResolutionStructuringInput(
            company_query=params.company_name,
            research_text=resolution_research.text,
        )
    )
    append_json(company_resolution.model_dump(mode="json"))

    company_research = await research_company(company_resolution)
    append_text(company_research.text)

    company_profile = CompanyProfileOutput(
        company_resolution=company_resolution,
        research_text=company_research.text,
    )

    await _send_status(status_callback, "Generating candidate use cases...\n")
    use_case_generation_input = GenAIUseCaseCandidateInput(
        company_profile=company_profile,
    )
    generated = await generate_genai_use_cases(use_case_generation_input)
    use_cases = GenAIUseCaseCandidatePool(use_cases=generated.use_cases)
    append_json(use_cases.model_dump(mode="json"))

    await _send_status(status_callback, "Scoring opportunities...\n")
    graded_use_cases = await grade_use_cases(
        GradeUseCasesInput(
            company_profile=company_profile,
            use_cases=use_cases.use_cases,
        )
    )
    append_json(graded_use_cases.model_dump(mode="json"))

    final_selection = await select_final_top_3(graded_use_cases)
    append_json({"final_top_3": final_selection.model_dump(mode="json")})

    await _send_status(status_callback, "Writing final report...\n")
    markdown_report = await write_markdown_report(
        MarkdownReportInput(
            company_profile=company_profile,
            final_selection=final_selection,
        )
    )
    append_text(markdown_report.markdown)

    return SparkstralWorkflowResult(outputs=outputs, final=markdown_report.markdown)
