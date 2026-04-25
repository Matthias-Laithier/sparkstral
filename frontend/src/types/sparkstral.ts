export type PipelineOutput = {
	id: number;
	kind: "text" | "json";
	text?: string | null;
	data?: Record<string, unknown> | null;
};

export type SparkstralWorkflowResult = {
	outputs: PipelineOutput[];
	final: GenAIUseCasesData;
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

export type PainPointItem = {
	title: string;
	description: string;
	prominence: number;
	sources: string[];
};

export type PainPointBundleData = {
	pain_points?: PainPointItem[];
};

export type GenAIUseCaseItem = {
	title: string;
	target_users: string[];
	business_problem: string;
	why_this_company: string;
	genai_solution: string;
	required_data: string;
	expected_impact: string;
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
	return Array.isArray(o.outputs);
}
