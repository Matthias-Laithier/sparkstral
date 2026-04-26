import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
		<article className="space-y-2 rounded-lg border border-sky-200/80 bg-sky-50/40 p-4">
			<div className="flex items-center justify-between gap-3">
				<p className="font-mono text-xs text-blue-900/70">
					Output {String(output.id).padStart(2, "0")}
				</p>
				<span className="rounded-md bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
					{output.kind}
				</span>
			</div>
			<pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md border border-slate-800/80 bg-slate-950 p-3 text-xs leading-relaxed text-slate-100">
				{stringify(value ?? "")}
			</pre>
		</article>
	);
}

function MarkdownReport({ markdown }: { markdown: string }) {
	return (
		<div className="max-h-[48rem] overflow-auto rounded-lg bg-white/95 p-5 text-sm leading-7 text-slate-700 shadow-inner shadow-sky-100/50">
			<ReactMarkdown
				remarkPlugins={[remarkGfm]}
				components={{
					h1: (props) => (
						<h1
							className="mb-4 border-b border-blue-200/80 pb-3 text-2xl font-semibold leading-tight text-blue-950"
							{...props}
						/>
					),
					h2: (props) => (
						<h2
							className="mb-3 mt-7 text-xl font-semibold leading-snug text-blue-950"
							{...props}
						/>
					),
					h3: (props) => (
						<h3
							className="mb-2 mt-5 text-lg font-semibold leading-snug text-slate-900"
							{...props}
						/>
					),
					p: (props) => <p className="my-3" {...props} />,
					ul: (props) => (
						<ul
							className="my-3 list-disc space-y-1 pl-6 marker:text-blue-600"
							{...props}
						/>
					),
					ol: (props) => (
						<ol
							className="my-3 list-decimal space-y-1 pl-6 marker:text-blue-600"
							{...props}
						/>
					),
					li: (props) => <li className="pl-1" {...props} />,
					a: (props) => (
						<a
							className="font-medium text-blue-700 underline decoration-blue-300/80 underline-offset-2 hover:text-blue-900"
							target="_blank"
							rel="noreferrer"
							{...props}
						/>
					),
					blockquote: (props) => (
						<blockquote
							className="my-4 border-l-4 border-sky-400 bg-sky-50/90 px-4 py-2 text-slate-700"
							{...props}
						/>
					),
					code: (props) => (
						<code
							className="rounded bg-sky-100/80 px-1.5 py-0.5 font-mono text-[0.85em] text-blue-950"
							{...props}
						/>
					),
					pre: (props) => (
						<pre
							className="my-4 overflow-auto rounded-lg border border-slate-700 bg-slate-950 p-4 text-xs leading-relaxed text-slate-100"
							{...props}
						/>
					),
					table: (props) => (
						<div className="my-4 overflow-x-auto rounded-lg border border-sky-200">
							<table
								className="w-full border-collapse text-left text-sm"
								{...props}
							/>
						</div>
					),
					th: (props) => (
						<th
							className="border border-sky-200 bg-sky-100/90 px-3 py-2 font-semibold text-blue-950"
							{...props}
						/>
					),
					td: (props) => (
						<td
							className="border border-sky-100 px-3 py-2 align-top"
							{...props}
						/>
					),
					hr: (props) => <hr className="my-6 border-sky-200" {...props} />,
				}}
			>
				{markdown}
			</ReactMarkdown>
		</div>
	);
}

export function WorkflowOutput({
	result,
}: {
	result: SparkstralWorkflowResult;
}) {
	return (
		<section className="space-y-6">
			<article className="rounded-xl border border-blue-200/90 bg-gradient-to-br from-white via-sky-50/50 to-blue-50/40 p-5 shadow-md shadow-blue-900/5">
				<h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-blue-800">
					GenAI opportunity report
				</h2>
				<MarkdownReport markdown={result.final} />
			</article>

			<details className="group rounded-xl border border-sky-200/90 bg-white/90 open:shadow-md open:shadow-sky-900/5">
				<summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-xl px-4 py-3.5 text-sm font-medium text-blue-950 hover:bg-sky-50/80 [&::-webkit-details-marker]:hidden">
					<span>Pipeline steps</span>
					<span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-normal text-blue-800">
						{result.outputs.length} outputs
					</span>
				</summary>
				<div className="space-y-3 border-t border-sky-100 px-4 pb-4 pt-3">
					{result.outputs.map((output) => (
						<OutputBlock key={output.id} output={output} />
					))}
				</div>
			</details>
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
		<div className="min-h-screen bg-gradient-to-b from-sky-100/40 via-slate-50 to-slate-100 p-4 py-10">
			<main className="mx-auto w-full max-w-4xl space-y-6 rounded-2xl border border-sky-200/80 bg-white/95 p-8 shadow-lg shadow-blue-900/10 backdrop-blur-sm">
				<div className="border-b border-sky-100 pb-6">
					<h1 className="bg-gradient-to-r from-blue-950 to-blue-700 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
						Sparkstral
					</h1>
					<p className="mt-2 text-sm text-slate-600">
						Research a company and open the GenAI opportunity report. Expand{" "}
						<span className="font-medium text-blue-800">Pipeline steps</span> to
						see intermediate JSON and text outputs.
					</p>
				</div>

				<form onSubmit={handleSubmit} className="space-y-3">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						placeholder="e.g. Stripe, Mistral AI, Notion..."
						disabled={loading}
						className="w-full rounded-xl border border-sky-200 bg-sky-50/30 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-shadow focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-400/30 disabled:bg-slate-50 disabled:text-slate-400"
					/>
					<button
						type="submit"
						disabled={loading || !input.trim()}
						className="w-full rounded-xl bg-gradient-to-r from-blue-700 to-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-900/20 transition hover:from-blue-800 hover:to-blue-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
					>
						{loading ? "Running pipeline..." : "Run analysis"}
					</button>
				</form>

				{loading && status && (
					<div className="flex items-center gap-2 text-sm text-blue-900/70">
						<span className="inline-block h-3 w-3 animate-pulse rounded-full bg-blue-500" />
						{status === "RUNNING" ? "Workflow running..." : status}
					</div>
				)}

				{result && <WorkflowOutput result={result} />}

				{unknownResult && (
					<pre className="overflow-auto whitespace-pre-wrap rounded-xl border border-amber-200/90 bg-amber-50/90 p-4 text-xs text-amber-950">
						{unknownResult}
					</pre>
				)}

				{error && (
					<div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
						{error}
					</div>
				)}
			</main>
		</div>
	);
}
