from src.activities import (
    generate_genai_use_cases,
    map_opportunities,
    research_company,
    research_company_resolution,
    research_pain_points,
    structure_company_profile,
    structure_company_resolution,
    structure_pain_points,
)
from src.schemas import (
    CompanyInput,
    CompanyProfileInput,
    CompanyProfileStructuringInput,
    CompanyResolutionInput,
    CompanyResolutionStructuringInput,
    GenAIUseCasesInput,
    OpportunityMapInput,
    PainPointResearchInput,
    PainPointStructuringInput,
    PipelineOutput,
    SparkstralWorkflowResult,
)
from src.utils import append_json_output, append_text_output


async def run_sparkstral_pipeline(params: CompanyInput) -> SparkstralWorkflowResult:
    outputs: list[PipelineOutput] = []

    resolution_research = await research_company_resolution(
        CompanyResolutionInput(company_query=params.company_name)
    )
    append_text_output(outputs, resolution_research.text)

    company_resolution = await structure_company_resolution(
        CompanyResolutionStructuringInput(
            company_query=params.company_name,
            research_text=resolution_research.text,
        )
    )
    append_json_output(outputs, company_resolution.model_dump(mode="json"))

    company_research = await research_company(
        CompanyProfileInput(company_query=company_resolution.resolved_name)
    )
    append_text_output(outputs, company_research.text)

    company_profile = await structure_company_profile(
        CompanyProfileStructuringInput(
            company_query=company_resolution.resolved_name,
            research_text=company_research.text,
        )
    )
    append_json_output(outputs, company_profile.model_dump(mode="json"))

    pain_research = await research_pain_points(
        PainPointResearchInput(company_profile=company_profile)
    )
    append_text_output(outputs, pain_research.text)

    pain_points = await structure_pain_points(
        PainPointStructuringInput(
            company_profile=company_profile,
            research_text=pain_research.text,
        )
    )
    append_json_output(outputs, pain_points.model_dump(mode="json"))

    opportunity_map = await map_opportunities(
        OpportunityMapInput(
            company_profile=company_profile,
            pain_points=pain_points,
        )
    )
    append_json_output(outputs, opportunity_map.model_dump(mode="json"))

    use_cases = await generate_genai_use_cases(
        GenAIUseCasesInput(
            company_profile=company_profile,
            pain_points=pain_points,
            opportunity_map=opportunity_map,
        )
    )
    append_json_output(outputs, use_cases.model_dump(mode="json"))

    return SparkstralWorkflowResult(outputs=outputs, final=use_cases)
