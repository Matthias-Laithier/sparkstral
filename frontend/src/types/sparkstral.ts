export type PipelineOutput = {
	id: number;
	kind: "text" | "json";
	text?: string | null;
	data?: Record<string, unknown> | null;
};

export type SparkstralWorkflowResult = {
	outputs: PipelineOutput[];
	final: string;
};

export type CompanyProfileData = {
	company_name?: string;
	industry?: string;
	business_lines?: string[];
	key_customers?: string[];
	strategic_priorities?: string[];
	evidence?: { claim: string; source: string }[];
	notes?: string;
};

export type SourceBackedMetric = {
	label: string;
	value: string;
	source_url: string;
	source_quote_or_evidence: string;
	applies_to:
		| "company"
		| "industry"
		| "similar_case"
		| "regulation"
		| "market"
		| "technology_benchmark";
	confidence: "low" | "medium" | "high";
};

export type PilotKPI = {
	kpi: string;
	why_it_matters: string;
	measurement_method: string;
	target_direction: "increase" | "decrease" | "maintain";
	baseline_needed: string;
};

export type GenAIUseCaseItem = {
	title: string;
	target_users: string[];
	business_problem: string;
	why_this_company: string;
	genai_solution: string;
	required_data: string;
	qualitative_impact: string;
	source_backed_metrics: SourceBackedMetric[];
	pilot_kpis: PilotKPI[];
	risks: string[];
};

export type GenAIUseCasesData = {
	use_cases?: GenAIUseCaseItem[];
};

export function isSparkstralResult(
	value: unknown,
): value is SparkstralWorkflowResult {
	if (value === null || typeof value !== "object") return false;
	const o = value as Record<string, unknown>;
	return Array.isArray(o.outputs) && typeof o.final === "string";
}
