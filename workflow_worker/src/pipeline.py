from functools import partial

from src.activities import (
    deduplicate_use_cases,
    generate_genai_use_cases,
    grade_use_cases,
    map_opportunities,
    red_team_use_cases,
    refine_use_cases,
    research_company,
    research_company_resolution,
    research_pain_points,
    select_final_top_3,
    select_initial_top_5,
    structure_company_profile,
    structure_company_resolution,
    structure_pain_points,
    write_final_report,
    write_markdown_report,
)
from src.schemas import (
    CompanyInput,
    CompanyProfileInput,
    CompanyProfileStructuringInput,
    CompanyResolutionInput,
    CompanyResolutionStructuringInput,
    DeduplicateUseCasesInput,
    FinalReportInput,
    GenAIUseCaseCandidateInput,
    GradeUseCasesInput,
    MarkdownReportInput,
    OpportunityMapInput,
    PainPointResearchInput,
    PainPointStructuringInput,
    PipelineOutput,
    RedTeamInput,
    RefineUseCasesInput,
    SparkstralWorkflowResult,
)
from src.utils import append_json_output, append_text_output


async def run_sparkstral_pipeline(params: CompanyInput) -> SparkstralWorkflowResult:
    outputs: list[PipelineOutput] = []
    append_text = partial(append_text_output, outputs)
    append_json = partial(append_json_output, outputs)

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

    company_research = await research_company(
        CompanyProfileInput(company_query=company_resolution.resolved_name)
    )
    append_text(company_research.text)

    company_profile = await structure_company_profile(
        CompanyProfileStructuringInput(
            company_query=company_resolution.resolved_name,
            research_text=company_research.text,
        )
    )
    append_json(company_profile.model_dump(mode="json"))

    pain_research = await research_pain_points(
        PainPointResearchInput(company_profile=company_profile)
    )
    append_text(pain_research.text)

    pain_points = await structure_pain_points(
        PainPointStructuringInput(
            company_profile=company_profile,
            research_text=pain_research.text,
        )
    )
    append_json(pain_points.model_dump(mode="json"))

    opportunity_map = await map_opportunities(
        OpportunityMapInput(
            company_profile=company_profile,
            pain_points=pain_points,
        )
    )
    append_json(opportunity_map.model_dump(mode="json"))

    use_cases = await generate_genai_use_cases(
        GenAIUseCaseCandidateInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
        )
    )
    append_json(use_cases.model_dump(mode="json"))

    deduplicated_use_cases = await deduplicate_use_cases(
        DeduplicateUseCasesInput(candidates=use_cases)
    )
    append_json(deduplicated_use_cases.model_dump(mode="json"))

    graded_use_cases = await grade_use_cases(
        GradeUseCasesInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
            use_cases=deduplicated_use_cases.use_cases,
        )
    )
    append_json(graded_use_cases.model_dump(mode="json"))

    initial_top_5 = await select_initial_top_5(graded_use_cases)
    append_json({"initial_top_5": initial_top_5.model_dump(mode="json")})

    red_team_review = await red_team_use_cases(
        RedTeamInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
            selected_use_cases=initial_top_5.selected,
        )
    )
    append_json({"red_team_review": red_team_review.model_dump(mode="json")})

    refined_use_cases = await refine_use_cases(
        RefineUseCasesInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
            selected_use_cases=initial_top_5.selected,
            red_team=red_team_review,
        )
    )
    append_json({"refined_use_cases": refined_use_cases.model_dump(mode="json")})

    refined_candidates = [
        item.refined_use_case for item in refined_use_cases.refined_use_cases
    ]
    final_graded_use_cases = await grade_use_cases(
        GradeUseCasesInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
            use_cases=refined_candidates,
        )
    )
    append_json({"final_grading": final_graded_use_cases.model_dump(mode="json")})

    final_selection = await select_final_top_3(final_graded_use_cases)
    append_json({"final_top_3": final_selection.model_dump(mode="json")})

    final_report = await write_final_report(
        FinalReportInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
            final_selection=final_selection,
        )
    )
    append_json({"final_report": final_report.model_dump(mode="json")})

    markdown_report = await write_markdown_report(
        MarkdownReportInput(final_report=final_report)
    )
    append_text(markdown_report.markdown)

    return SparkstralWorkflowResult(outputs=outputs, final=markdown_report.markdown)
