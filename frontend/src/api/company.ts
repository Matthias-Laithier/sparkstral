import {
	isSparkstralResult,
	type SparkstralWorkflowResult,
} from "../types/sparkstral";

export type TriggerResponse = {
	execution_id: string;
	status: string;
};

export type StatusResponse = {
	execution_id: string;
	status: string;
	result: unknown;
};

export async function triggerCompanyDescription(
	companyName: string,
): Promise<TriggerResponse> {
	const response = await fetch("/api/company", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ company_name: companyName }),
	});

	if (!response.ok) {
		throw new Error("Failed to start workflow");
	}

	return (await response.json()) as TriggerResponse;
}

export async function getExecutionStatus(
	executionId: string,
): Promise<StatusResponse> {
	const response = await fetch(`/api/company/${executionId}`);

	if (!response.ok) {
		throw new Error("Failed to fetch execution status");
	}

	return (await response.json()) as StatusResponse;
}

/** Unwrap common Mistral or proxy nesting: `{ outputs: [...] }` or `{ result: { ... } }`. */
function extractSparkstralPayload(value: unknown): unknown {
	if (value === null || value === undefined) return value;
	if (typeof value === "string") {
		try {
			return extractSparkstralPayload(JSON.parse(value) as unknown);
		} catch {
			return value;
		}
	}
	if (isSparkstralResult(value)) {
		return value;
	}
	if (typeof value === "object" && value !== null && "result" in value) {
		return extractSparkstralPayload((value as { result: unknown }).result);
	}
	/* Mistral LeChat / ChatAssistantWorkflowOutput: payload lives under structuredContent */
	if (
		typeof value === "object" &&
		value !== null &&
		"structuredContent" in value
	) {
		return extractSparkstralPayload(
			(value as { structuredContent: unknown }).structuredContent,
		);
	}
	return value;
}

/** When status is COMPLETED, `result` may be a Sparkstral payload. */
export function asSparkstralResult(
	result: unknown,
): SparkstralWorkflowResult | null {
	const payload = extractSparkstralPayload(result);
	return isSparkstralResult(payload) ? payload : null;
}
