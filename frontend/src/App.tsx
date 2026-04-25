import { useCallback, useEffect, useRef, useState } from "react";
import {
	asSparkstralResult,
	getExecutionStatus,
	triggerCompanyDescription,
} from "./api/company";
import type {
	PipelineOutput,
	SparkstralWorkflowResult,
} from "./types/sparkstral";

const TERMINAL_STATUSES = new Set([
	"COMPLETED",
	"FAILED",
	"CANCELED",
	"TERMINATED",
	"TIMED_OUT",
]);

const POLL_INTERVAL_MS = 2000;

function stringify(value: unknown): string {
	if (typeof value === "string") return value;
	return JSON.stringify(value, null, 2);
}

function OutputBlock({ output }: { output: PipelineOutput }) {
	const value = output.kind === "text" ? output.text : output.data;
	return (
		<article className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
			<div className="flex items-center justify-between gap-3">
				<p className="text-xs font-mono text-slate-500">
					Output {String(output.id).padStart(2, "0")}
				</p>
				<span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
					{output.kind}
				</span>
			</div>
			<pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-slate-950 p-3 text-xs leading-relaxed text-slate-100">
				{stringify(value ?? "")}
			</pre>
		</article>
	);
}

export function WorkflowOutput({
	result,
}: {
	result: SparkstralWorkflowResult;
}) {
	return (
		<section className="space-y-4">
			<div className="space-y-3">
				{result.outputs.map((output) => (
					<OutputBlock key={output.id} output={output} />
				))}
			</div>
			<article className="rounded-lg border border-violet-200 bg-violet-50 p-4 space-y-2">
				<p className="text-xs font-mono text-violet-700">Final result</p>
				<pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs leading-relaxed text-slate-800">
					{stringify(result.final)}
				</pre>
			</article>
		</section>
	);
}

export default function App() {
	const [input, setInput] = useState("");
	const [status, setStatus] = useState<string | null>(null);
	const [rawResult, setRawResult] = useState<unknown>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);
	const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

	const stopPolling = useCallback(() => {
		if (pollRef.current !== null) {
			clearInterval(pollRef.current);
			pollRef.current = null;
		}
	}, []);

	useEffect(() => {
		return () => {
			stopPolling();
		};
	}, [stopPolling]);

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		const companyName = input.trim();
		if (!companyName) return;

		stopPolling();
		setLoading(true);
		setStatus(null);
		setRawResult(null);
		setError(null);

		let executionId: string;

		try {
			const trigger = await triggerCompanyDescription(companyName);
			executionId = trigger.execution_id;
			setStatus(trigger.status);
		} catch {
			setError("Could not start the workflow. Is the backend running?");
			setLoading(false);
			return;
		}

		pollRef.current = setInterval(async () => {
			try {
				const data = await getExecutionStatus(executionId);
				setStatus(data.status);

				if (TERMINAL_STATUSES.has(data.status)) {
					stopPolling();
					setLoading(false);

					if (data.status === "COMPLETED") {
						setRawResult(data.result);
					} else {
						setError(`Workflow ended with status: ${data.status}`);
					}
				}
			} catch {
				stopPolling();
				setLoading(false);
				setError("Lost connection while polling for the result.");
			}
		}, POLL_INTERVAL_MS);
	}

	const result = rawResult != null ? asSparkstralResult(rawResult) : null;
	const unknownResult =
		rawResult != null && result == null ? stringify(rawResult) : null;

	return (
		<div className="min-h-screen bg-slate-50 p-4 py-10">
			<main className="mx-auto w-full max-w-4xl space-y-6 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
				<div>
					<h1 className="text-2xl font-semibold text-slate-900">Sparkstral</h1>
					<p className="mt-1 text-sm text-slate-500">
						Run the research pipeline and inspect each raw text or JSON output.
					</p>
				</div>

				<form onSubmit={handleSubmit} className="space-y-3">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						placeholder="e.g. Stripe, Mistral AI, Notion..."
						disabled={loading}
						className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:bg-slate-50 disabled:text-slate-400"
					/>
					<button
						type="submit"
						disabled={loading || !input.trim()}
						className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
					>
						{loading ? "Running pipeline..." : "Run analysis"}
					</button>
				</form>

				{loading && status && (
					<div className="flex items-center gap-2 text-sm text-slate-500">
						<span className="inline-block h-3 w-3 animate-pulse rounded-full bg-slate-400" />
						{status === "RUNNING" ? "Workflow running..." : status}
					</div>
				)}

				{result && <WorkflowOutput result={result} />}

				{unknownResult && (
					<pre className="overflow-auto whitespace-pre-wrap rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-950">
						{unknownResult}
					</pre>
				)}

				{error && (
					<div className="rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
						{error}
					</div>
				)}
			</main>
		</div>
	);
}
