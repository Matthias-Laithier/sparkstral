export type SparkstralStep = {
	id: number;
	label: string;
	phase: "research" | "structure";
	content?: string | null;
	data?: Record<string, unknown> | null;
};

export type SparkstralWorkflowResult = {
	steps: SparkstralStep[];
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

export function isSparkstralResult(
	value: unknown,
): value is SparkstralWorkflowResult {
	if (value === null || typeof value !== "object") return false;
	const o = value as Record<string, unknown>;
	return Array.isArray(o.steps);
}
