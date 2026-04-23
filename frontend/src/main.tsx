import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

type BoundaryState = { error: Error | null };

class ErrorBoundary extends React.Component<
	{ children: React.ReactNode },
	BoundaryState
> {
	state: BoundaryState = { error: null };

	static getDerivedStateFromError(error: Error): BoundaryState {
		return { error };
	}

	render() {
		if (this.state.error) {
			return (
				<div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
					<div className="w-full max-w-lg bg-white rounded-2xl shadow-sm border border-red-200 p-8 space-y-3">
						<p className="text-sm font-medium text-red-700">Something went wrong</p>
						<p className="text-sm text-gray-500">{this.state.error.message}</p>
						<button
							type="button"
							onClick={() => window.location.reload()}
							className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
						>
							Reload
						</button>
					</div>
				</div>
			);
		}
		return this.props.children;
	}
}

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

createRoot(root).render(
	<React.StrictMode>
		<ErrorBoundary>
			<App />
		</ErrorBoundary>
	</React.StrictMode>,
);
