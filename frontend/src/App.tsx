import { useEffect, useRef, useState } from "react";
import { getExecutionStatus, triggerCompanyDescription } from "./api/company";

const TERMINAL_STATUSES = new Set([
	"COMPLETED",
	"FAILED",
	"CANCELED",
	"TERMINATED",
	"TIMED_OUT",
]);

const POLL_INTERVAL_MS = 2000;

export default function App() {
	const [input, setInput] = useState("");
	const [status, setStatus] = useState<string | null>(null);
	const [result, setResult] = useState<string | null>(null);
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
		setResult(null);
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
						const raw = data.result;
						setResult(
							raw == null
								? "No description returned."
								: typeof raw === "string"
									? raw
									: JSON.stringify(raw),
						);
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

	return (
		<div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
			<div className="w-full max-w-lg bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6">
				<div>
					<h1 className="text-2xl font-semibold text-gray-800">
						Company Lookup
					</h1>
					<p className="mt-1 text-sm text-gray-500">
						Enter a company name to get a short description of what it does.
					</p>
				</div>

				<form onSubmit={handleSubmit} className="space-y-3">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						placeholder="e.g. Stripe, Mistral AI, Notion…"
						disabled={isSearching}
						className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400"
					/>
					<button
						type="submit"
						disabled={isSearching || !input.trim()}
						className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						{isSearching ? "Searching…" : "Search"}
					</button>
				</form>

				{isSearching && status && (
					<div className="flex items-center gap-2 text-sm text-gray-500">
						<span className="inline-block w-3 h-3 rounded-full bg-blue-400 animate-pulse" />
						{status === "RUNNING" ? "Searching the web…" : status}
					</div>
				)}

				{result && (
					<div className="rounded-lg bg-blue-50 border border-blue-100 px-4 py-3 text-sm text-blue-900 leading-relaxed">
						{result}
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
