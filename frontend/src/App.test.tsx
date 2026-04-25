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

	it("renders generic workflow outputs and final markdown", () => {
		render(
			<WorkflowOutput
				result={{
					outputs: [
						{ id: 1, kind: "text", text: "research notes" },
						{ id: 2, kind: "json", data: { company_name: "Acme" } },
					],
					final:
						"# Acme Corporation GenAI Opportunity Report\n\n## Executive Summary\n\n- Automate onboarding\n- Improve support",
				}}
			/>,
		);

		expect(screen.getByText("research notes")).toBeDefined();
		expect(screen.getByText(/company_name/)).toBeDefined();
		expect(screen.getByText("Final result")).toBeDefined();
		expect(
			screen.getByRole("heading", {
				level: 1,
				name: "Acme Corporation GenAI Opportunity Report",
			}),
		).toBeDefined();
		expect(
			screen.getByRole("heading", { level: 2, name: "Executive Summary" }),
		).toBeDefined();
		expect(screen.getByText("Automate onboarding").tagName).toBe("LI");
		expect(screen.queryByText(/^# Acme Corporation/)).toBeNull();
	});
});
