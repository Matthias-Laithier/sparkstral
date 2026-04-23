import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
	it("renders the input and send button", () => {
		render(<App />);
		expect(screen.getByPlaceholderText("Type something…")).toBeDefined();
		expect(screen.getByRole("button", { name: "Send" })).toBeDefined();
	});
});
