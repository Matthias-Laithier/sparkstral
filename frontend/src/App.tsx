import { useEffect, useRef, useState } from "react";
import {
	asSparkstralResult,
	getExecutionStatus,
	triggerCompanyDescription,
} from "./api/company";
import type {
	CompanyProfileData,
	PainPointBundleData,
	PainPointItem,
	SparkstralStep,
} from "./types/sparkstral";

const TERMINAL_STATUSES = new Set([
	"COMPLETED",
	"FAILED",
	"CANCELED",
	"TERMINATED",
	"TIMED_OUT",
]);

const POLL_INTERVAL_MS = 2000;

function CompanyProfileView({ data }: { data: CompanyProfileData }) {
	return (
		<div className="space-y-3 text-sm text-slate-800">
			<div className="flex flex-wrap gap-2 items-baseline">
				<span className="font-semibold text-slate-900">
					{data.company_name || "—"}
				</span>
			</div>
			{data.industry ? (
				<p>
					<span className="text-slate-500">Industry </span>
					{data.industry}
				</p>
			) : null}
			{data.notes ? (
				<p className="text-amber-800 bg-amber-50 border border-amber-100 rounded-md px-3 py-2">
					{data.notes}
				</p>
			) : null}
			{data.business_lines && data.business_lines.length > 0 && (
				<div>
					<p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
						Business lines
					</p>
					<ul className="list-disc list-inside text-slate-700">
						{data.business_lines.map((x) => (
							<li key={x}>{x}</li>
						))}
					</ul>
				</div>
			)}
			{data.evidence && data.evidence.length > 0 && (
				<div>
					<p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
						Evidence
					</p>
					<ul className="space-y-2">
						{data.evidence.map((e) => (
							<li
								key={`${e.source}::${e.claim}`}
								className="border-l-2 border-slate-200 pl-3"
							>
								<p className="text-slate-800">{e.claim}</p>
								<a
									href={e.source}
									className="text-xs text-blue-600 hover:underline break-all"
									target="_blank"
									rel="noreferrer"
								>
									{e.source}
								</a>
							</li>
						))}
					</ul>
				</div>
			)}
		</div>
	);
}

function PainPointCard({ item }: { item: PainPointItem }) {
	return (
		<div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
			<div className="flex items-start justify-between gap-2">
				<h3 className="font-medium text-slate-900">{item.title}</h3>
				<span
					className="shrink-0 text-xs font-semibold tabular-nums rounded-md bg-slate-100 text-slate-700 px-2 py-0.5"
					title="Prominence 1–10"
				>
					{item.prominence}
				</span>
			</div>
			<p className="mt-2 text-sm text-slate-600 leading-relaxed">
				{item.description}
			</p>
			{item.sources && item.sources.length > 0 && (
				<ul className="mt-3 space-y-1">
					<p className="text-xs text-slate-500">Sources</p>
					{item.sources.map((s) => (
						<li key={s}>
							<a
								href={s}
								className="text-xs text-blue-600 hover:underline break-all"
								target="_blank"
								rel="noreferrer"
							>
								{s}
							</a>
						</li>
					))}
				</ul>
			)}
		</div>
	);
}

function PainPointsView({ data }: { data: PainPointBundleData }) {
	const items = data.pain_points ?? [];
	if (items.length === 0) {
		return <p className="text-sm text-slate-500">No pain points returned.</p>;
	}
	return (
		<div className="space-y-3">
			{items.map((item) => (
				<PainPointCard key={`${item.title}::${item.description}`} item={item} />
			))}
		</div>
	);
}

function renderStructureBody(step: SparkstralStep) {
	const data = step.data;
	if (data == null) {
		return <p className="text-sm text-slate-500">No structured data.</p>;
	}
	if (step.id === 2) {
		return <CompanyProfileView data={data as CompanyProfileData} />;
	}
	if (step.id === 4) {
		return <PainPointsView data={data as PainPointBundleData} />;
	}
	if ("pain_points" in data) {
		return <PainPointsView data={data as PainPointBundleData} />;
	}
	if ("company_name" in data || "evidence" in data) {
		return <CompanyProfileView data={data as CompanyProfileData} />;
	}
	return (
		<pre className="text-xs overflow-x-auto text-slate-700 bg-slate-50 p-3 rounded-md border border-slate-200">
			{JSON.stringify(data, null, 2)}
		</pre>
	);
}

function StepsTimeline({ steps }: { steps: SparkstralStep[] }) {
	return (
		<ol className="space-y-6 border-l-2 border-slate-200 ml-2 pl-4">
			{steps.map((step) => (
				<li key={step.id} className="relative -ml-[2px] pl-0">
					<div className="absolute -left-[1.1rem] top-2 w-2.5 h-2.5 rounded-full border-2 border-slate-200 bg-white" />
					<div className="space-y-2">
						<div className="flex flex-wrap items-center gap-2">
							<span className="text-xs font-mono text-slate-400">
								{String(step.id).padStart(2, "0")}
							</span>
							<h2 className="text-sm font-semibold text-slate-900">
								{step.label}
							</h2>
							<span
								className={
									step.phase === "research"
										? "text-xs font-medium px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700"
										: "text-xs font-medium px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800"
								}
							>
								{step.phase}
							</span>
						</div>
						{step.phase === "research" && step.content != null && (
							<div className="max-h-72 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3">
								<pre className="text-xs text-slate-800 whitespace-pre-wrap font-mono leading-relaxed">
									{step.content}
								</pre>
							</div>
						)}
						{step.phase === "structure" && renderStructureBody(step)}
					</div>
				</li>
			))}
		</ol>
	);
}

export default function App() {
	const [input, setInput] = useState("");
	const [status, setStatus] = useState<string | null>(null);
	const [rawResult, setRawResult] = useState<unknown>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);
	const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

	function stopPolling() {
		if (pollRef.current !== null) {
			clearInterval(pollRef.current);
			pollRef.current = null;
		}
	}

	useEffect(() => {
		return () => {
			if (pollRef.current !== null) clearInterval(pollRef.current);
		};
	}, []);

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		if (!input.trim()) return;

		stopPolling();
		setLoading(true);
		setStatus(null);
		setRawResult(null);
		setError(null);

		let executionId: string;

		try {
			const trigger = await triggerCompanyDescription(input.trim());
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

	const isSearching = loading;
	const pipelined = rawResult != null ? asSparkstralResult(rawResult) : null;
	const legacyText =
		rawResult != null && !pipelined
			? typeof rawResult === "string"
				? rawResult
				: JSON.stringify(rawResult, null, 2)
			: null;

	return (
		<div className="min-h-screen bg-slate-50 flex items-start justify-center p-4 py-10">
			<div className="w-full max-w-3xl bg-white rounded-2xl shadow-sm border border-slate-200 p-8 space-y-6">
				<div>
					<h1 className="text-2xl font-semibold text-slate-900">Sparkstral</h1>
					<p className="mt-1 text-sm text-slate-500">
						Web research and structured extraction: company profile, then
						industry pain points — each step shown in order when the run
						completes.
					</p>
				</div>

				<form onSubmit={handleSubmit} className="space-y-3">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						placeholder="e.g. Stripe, Mistral AI, Notion…"
						disabled={isSearching}
						className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-transparent disabled:bg-slate-50 disabled:text-slate-400"
					/>
					<button
						type="submit"
						disabled={isSearching || !input.trim()}
						className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						{isSearching ? "Running pipeline…" : "Run analysis"}
					</button>
				</form>

				{isSearching && status && (
					<div className="flex items-center gap-2 text-sm text-slate-500">
						<span className="inline-block w-3 h-3 rounded-full bg-slate-400 animate-pulse" />
						{status === "RUNNING" ? "Workflow running…" : status}
					</div>
				)}

				{pipelined && (
					<div className="rounded-xl border border-slate-200 bg-slate-50/50 p-5">
						<StepsTimeline steps={pipelined.steps} />
					</div>
				)}

				{legacyText && (
					<div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
						<p className="text-xs font-medium text-amber-800 mb-2">
							Legacy / non-timeline result
						</p>
						<pre className="whitespace-pre-wrap font-mono text-xs overflow-x-auto">
							{legacyText}
						</pre>
					</div>
				)}

				{error && (
					<div className="rounded-lg bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-700">
						{error}
					</div>
				)}
			</div>
		</div>
	);
}
