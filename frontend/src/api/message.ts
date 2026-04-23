export type MessageResponse = {
	message: string;
};

export async function sendMessage(input: string): Promise<MessageResponse> {
	const response = await fetch("/api/message", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ input }),
	});

	if (!response.ok) {
		throw new Error("Request failed");
	}

	return (await response.json()) as MessageResponse;
}
