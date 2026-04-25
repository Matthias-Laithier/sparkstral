import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App, { WorkflowOutput } from "./App";

describe("App", () => {
	it("renders the company input and run button", () => {
		render(<App />);
		expect(
			screen.getByPlaceholderText("e.g. Stripe, Mistral AI, Notion..."),
		).toBeDefined();
		expect(screen.getByRole("button", { name: "Run analysis" })).toBeDefined();
	});

	it("renders generic workflow outputs", () => {
		render(
			<WorkflowOutput
				result={{
					outputs: [
						{ id: 1, kind: "text", text: "research notes" },
						{ id: 2, kind: "json", data: { company_name: "Acme" } },
					],
					final:
						"# Acme Corporation GenAI Opportunity Report\n\n## Executive Summary",
				}}
			/>,
		);

		expect(screen.getByText("research notes")).toBeDefined();
		expect(screen.getByText(/company_name/)).toBeDefined();
		expect(screen.getByText("Final result")).toBeDefined();
		expect(screen.getByText(/Executive Summary/)).toBeDefined();
	});
});
