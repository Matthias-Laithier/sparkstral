import { useState } from "react";
import { sendMessage } from "./api/message";

export default function App() {
	const [input, setInput] = useState("");
	const [reply, setReply] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		if (!input.trim()) return;

		setLoading(true);
		setReply(null);
		setError(null);

		try {
			const data = await sendMessage(input.trim());
			setReply(data.message);
		} catch {
			setError("Something went wrong. Is the backend running?");
		} finally {
			setLoading(false);
		}
	}

	return (
		<div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
			<div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6">
				<h1 className="text-2xl font-semibold text-gray-800">Sparkstral</h1>

				<form onSubmit={handleSubmit} className="space-y-3">
					<input
						type="text"
						value={input}
						onChange={(e) => setInput(e.target.value)}
						placeholder="Type something…"
						className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
					<button
						type="submit"
						disabled={loading || !input.trim()}
						className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						{loading ? "Sending…" : "Send"}
					</button>
				</form>

				{reply && (
					<div className="rounded-lg bg-blue-50 border border-blue-100 px-4 py-3 text-sm text-blue-800">
						{reply}
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
