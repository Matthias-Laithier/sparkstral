from src.core.schemas import FactCheckOutput, GenAIUseCaseCandidate


def apply_fact_check(
    use_case: GenAIUseCaseCandidate,
    fact_check: FactCheckOutput,
) -> GenAIUseCaseCandidate:
    """Patch the free-text fields of a use case with fact-checked versions."""
    return use_case.model_copy(
        update={
            "business_problem": fact_check.business_problem,
            "genai_solution": fact_check.genai_solution,
            "why_this_company": fact_check.why_this_company,
            "why_iconic": fact_check.why_iconic,
            "feasibility_notes": fact_check.feasibility_notes,
            "required_data": fact_check.required_data,
        }
    )
