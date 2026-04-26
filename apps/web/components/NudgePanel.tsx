"use client";

import { useEffect, useState } from "react";
import { Lightbulb, X, CheckCircle, ThumbsUp, ThumbsDown } from "lucide-react";

interface Nudge {
	id: string;
	title: string;
	suggestion: string;
	priority: string;
	priority_score: number;
	confidence: number;
	route: string;
	transcript_chunk: string;
	created_at: string;
}

interface NudgePanelProps {
	callId: string;
	product: string;
	apiBaseUrl: string;
}

export function NudgePanel({ callId, product, apiBaseUrl }: NudgePanelProps) {
	const [nudges, setNudges] = useState<Nudge[]>([]);
	const [dismissed, setDismissed] = useState<Set<string>>(new Set());
	const [used, setUsed] = useState<Set<string>>(new Set());
	const [loading, setLoading] = useState(false);

	// Poll for new nudges every 2 seconds during active call
	useEffect(() => {
		const fetchNudges = async () => {
			try {
				setLoading(true);
				const response = await fetch(
					`${apiBaseUrl}/api/nudges?call_id=${callId}&emitted=true`,
				);
				if (response.ok) {
					const data: Nudge[] = await response.json();
					setNudges(data.reverse()); // newest first
				}
			} catch (error) {
				console.error("Error fetching nudges:", error);
			} finally {
				setLoading(false);
			}
		};

		fetchNudges();
		const interval = setInterval(fetchNudges, 2000);
		return () => clearInterval(interval);
	}, [callId, apiBaseUrl]);

	const handleDismiss = async (nudgeId: string) => {
		try {
			await fetch(`${apiBaseUrl}/api/nudges/${nudgeId}/history`, {
				method: "PATCH",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ dismissed: true, viewed: true }),
			});
			setDismissed((prev) => new Set([...prev, nudgeId]));
		} catch (error) {
			console.error("Error dismissing nudge:", error);
		}
	};

	const handleUse = async (nudgeId: string) => {
		try {
			await fetch(`${apiBaseUrl}/api/nudges/${nudgeId}/history`, {
				method: "PATCH",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ used: true, viewed: true }),
			});
			setUsed((prev) => new Set([...prev, nudgeId]));
		} catch (error) {
			console.error("Error marking nudge as used:", error);
		}
	};

	const handleFeedback = async (nudgeId: string, helped: boolean) => {
		try {
			await fetch(`${apiBaseUrl}/api/nudges/${nudgeId}/history`, {
				method: "PATCH",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ helped, viewed: true }),
			});
		} catch (error) {
			console.error("Error submitting feedback:", error);
		}
	};

	const visibleNudges = nudges.filter((n) => !dismissed.has(n.id));

	if (visibleNudges.length === 0) {
		return (
			<div className="p-4 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl">
				<div className="flex items-center gap-2 text-slate-400 text-sm">
					<Lightbulb className="w-4 h-4" />
					<span>No suggestions yet...</span>
				</div>
			</div>
		);
	}

	return (
		<div className="space-y-3">
			<div className="flex items-center gap-2 mb-2">
				<Lightbulb className="w-5 h-5 text-yellow-400" />
				<h3 className="text-sm font-semibold text-white uppercase tracking-wide">
					Agent Assists ({visibleNudges.length})
				</h3>
			</div>

			{visibleNudges.map((nudge) => {
				const isUsed = used.has(nudge.id);
				const priorityColor =
					nudge.priority === "high"
						? "border-red-500/50 bg-red-500/10"
						: nudge.priority === "medium"
						? "border-yellow-500/50 bg-yellow-500/10"
						: "border-blue-500/50 bg-blue-500/10";

				return (
					<div
						key={nudge.id}
						className={`p-4 backdrop-blur-sm border rounded-xl transition-all ${priorityColor} ${
							isUsed ? "opacity-60" : ""
						}`}
					>
						<div className="flex items-start justify-between gap-2 mb-2">
							<div className="flex-1">
								<div className="flex items-center gap-2 mb-1">
									<span className="text-xs font-bold text-white uppercase">
										{nudge.title}
									</span>
									{isUsed && (
										<CheckCircle className="w-4 h-4 text-green-400" />
									)}
								</div>
								<p className="text-xs text-slate-300 mb-2">
									{nudge.suggestion}
								</p>
								<div className="flex items-center gap-3 text-xs text-slate-400">
									<span>Route: {nudge.route}</span>
									<span>•</span>
									<span>Confidence: {(nudge.confidence * 100).toFixed(0)}%</span>
								</div>
							</div>
							<button
								onClick={() => handleDismiss(nudge.id)}
								className="p-1 hover:bg-white/10 rounded-lg transition-colors"
								title="Dismiss"
							>
								<X className="w-4 h-4 text-slate-400" />
							</button>
						</div>

						{/* Trigger Context */}
						<div className="mt-2 p-2 bg-black/20 rounded-lg">
							<p className="text-xs text-slate-400 italic">
								Context: "{nudge.transcript_chunk}"
							</p>
						</div>

						{/* Actions */}
						<div className="mt-3 flex items-center gap-2">
							{!isUsed && (
								<button
									onClick={() => handleUse(nudge.id)}
									className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-medium transition-all"
								>
									✓ Used This
								</button>
							)}
							{isUsed && (
								<>
									<button
										onClick={() => handleFeedback(nudge.id, true)}
										className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-all flex items-center gap-1"
										title="This helped"
									>
										<ThumbsUp className="w-3 h-3" />
										Helped
									</button>
									<button
										onClick={() => handleFeedback(nudge.id, false)}
										className="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-xs font-medium transition-all flex items-center gap-1"
										title="Didn't help"
									>
										<ThumbsDown className="w-3 h-3" />
										Not Helpful
									</button>
								</>
							)}
						</div>
					</div>
				);
			})}
		</div>
	);
}
