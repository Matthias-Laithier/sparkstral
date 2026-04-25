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
					final: {
						use_cases: [
							{
								title: "Use case 1",
								target_users: ["Ops"],
								business_problem: "Problem",
								why_this_company: "Fit",
								genai_solution: "Solution",
								required_data: "Data",
								expected_impact: "Impact",
								risks: ["Risk"],
							},
							{
								title: "Use case 2",
								target_users: ["Sales"],
								business_problem: "Problem",
								why_this_company: "Fit",
								genai_solution: "Solution",
								required_data: "Data",
								expected_impact: "Impact",
								risks: ["Risk"],
							},
							{
								title: "Use case 3",
								target_users: ["Product"],
								business_problem: "Problem",
								why_this_company: "Fit",
								genai_solution: "Solution",
								required_data: "Data",
								expected_impact: "Impact",
								risks: ["Risk"],
							},
						],
					},
				}}
			/>,
		);

		expect(screen.getByText("research notes")).toBeDefined();
		expect(screen.getByText(/company_name/)).toBeDefined();
		expect(screen.getByText("Final result")).toBeDefined();
	});
});
