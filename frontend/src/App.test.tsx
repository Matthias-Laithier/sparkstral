import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
	it("renders the company input and run button", () => {
		render(<App />);
		expect(
			screen.getByPlaceholderText("e.g. Stripe, Mistral AI, Notion…"),
		).toBeDefined();
		expect(screen.getByRole("button", { name: "Run analysis" })).toBeDefined();
	});
});
