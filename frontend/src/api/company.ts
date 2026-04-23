export type TriggerResponse = {
	execution_id: string;
	status: string;
};

export type StatusResponse = {
	execution_id: string;
	status: string;
	result: string | null;
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
