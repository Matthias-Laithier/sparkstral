from src.activities import (
    generate_genai_use_cases,
    research_company,
    research_pain_points,
    structure_company_profile,
    structure_pain_points,
)
from src.schemas import (
    CompanyInput,
    CompanyProfileInput,
    CompanyProfileStructuringInput,
    GenAIUseCasesInput,
    PainPointResearchInput,
    PainPointStructuringInput,
    PipelineOutput,
    SparkstralWorkflowResult,
)
from src.utils import append_json_output, append_text_output


async def run_sparkstral_pipeline(params: CompanyInput) -> SparkstralWorkflowResult:
    outputs: list[PipelineOutput] = []

    company_research = await research_company(
        CompanyProfileInput(company_query=params.company_name)
    )
    append_text_output(outputs, company_research.text)

    company_profile = await structure_company_profile(
        CompanyProfileStructuringInput(
            company_query=params.company_name,
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

    use_cases = await generate_genai_use_cases(
        GenAIUseCasesInput(
            company_profile=company_profile,
            pain_points=pain_points,
        )
    )
    append_json_output(outputs, use_cases.model_dump(mode="json"))

    return SparkstralWorkflowResult(outputs=outputs, final=use_cases)
