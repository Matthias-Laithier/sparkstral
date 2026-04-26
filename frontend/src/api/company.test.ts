import { describe, expect, it } from "vitest";
import { asSparkstralResult } from "./company";

describe("asSparkstralResult", () => {
	it("accepts flat SparkstralWorkflowResult", () => {
		const payload = {
			outputs: [{ id: 1, kind: "text" as const, text: "step" }],
			final: "# Report\n\nHello.",
		};
		expect(asSparkstralResult(payload)).toEqual(payload);
	});

	it("unwraps Mistral ChatAssistantWorkflowOutput (structuredContent)", () => {
		const inner = {
			outputs: [{ id: 1, kind: "text" as const, text: "research" }],
			final: "# Done\n\nOK.",
		};
		const wrapped = {
			content: [{ type: "text", text: "Sparkstral analysis complete." }],
			structuredContent: inner,
			isError: null,
		};
		expect(asSparkstralResult(wrapped)).toEqual(inner);
	});

	it("unwraps nested result envelope then structuredContent", () => {
		const inner = {
			outputs: [],
			final: "# Only final",
		};
		expect(
			asSparkstralResult({
				result: { structuredContent: inner },
			}),
		).toEqual(inner);
	});

	it("returns null when shape is unknown", () => {
		expect(asSparkstralResult({ foo: 1 })).toBeNull();
		expect(asSparkstralResult({ outputs: [], missingFinal: true })).toBeNull();
	});
});
