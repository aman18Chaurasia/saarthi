"use client";

import { useEffect, useState } from "react";
import { Lightbulb, X, CheckCircle, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
	const [collapsed, setCollapsed] = useState(false);

	useEffect(() => {
		const fetchNudges = async () => {
			try {
				const response = await fetch(
					`${apiBaseUrl}/api/nudges?call_id=${callId}&emitted=true`,
				);
				if (response.ok) {
					const data: Nudge[] = await response.json();
					setNudges(data.reverse());
				}
			} catch (error) {
				console.error("Error fetching nudges:", error);
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
		return null;
	}

	const getPriorityStyle = (priority: string) => {
		switch (priority) {
			case "high":
				return "border-red-500/50 bg-red-500/10 shadow-[0_0_20px_rgba(239,68,68,0.3)]";
			case "medium":
				return "border-yellow-500/50 bg-yellow-500/10 shadow-[0_0_15px_rgba(234,179,8,0.2)]";
			default:
				return "border-blue-500/50 bg-blue-500/10 shadow-[0_0_15px_rgba(59,130,246,0.2)]";
		}
	};

	const getPriorityColor = (priority: string) => {
		switch (priority) {
			case "high":
				return "text-red-400";
			case "medium":
				return "text-yellow-400";
			default:
				return "text-blue-400";
		}
	};

	return (
		<motion.div
			initial={{ y: 20, opacity: 0 }}
			animate={{ y: 0, opacity: 1 }}
			className="w-full"
		>
			{/* Header */}
			<div
				className="flex items-center justify-between p-4 bg-white/5 backdrop-blur-md border border-white/10 rounded-t-2xl cursor-pointer hover:bg-white/10 transition-colors"
				onClick={() => setCollapsed(!collapsed)}
			>
				<div className="flex items-center gap-3">
					<Lightbulb className="w-5 h-5 text-yellow-400" />
					<h3 className="text-sm font-semibold text-white uppercase tracking-wide">
						Agent Assists
					</h3>
					<span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-bold rounded-full border border-yellow-500/30">
						{visibleNudges.length}
					</span>
				</div>
				{collapsed ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
			</div>

			{/* Nudges */}
			<AnimatePresence>
				{!collapsed && (
					<motion.div
						initial={{ height: 0, opacity: 0 }}
						animate={{ height: "auto", opacity: 1 }}
						exit={{ height: 0, opacity: 0 }}
						className="space-y-3 p-4 bg-white/5 backdrop-blur-md border-x border-b border-white/10 rounded-b-2xl max-h-[400px] overflow-y-auto"
					>
						{visibleNudges.map((nudge, idx) => {
							const isUsed = used.has(nudge.id);
							const priorityStyle = getPriorityStyle(nudge.priority);
							const priorityColor = getPriorityColor(nudge.priority);

							return (
								<motion.div
									key={nudge.id}
									initial={{ x: -20, opacity: 0 }}
									animate={{ x: 0, opacity: 1 }}
									exit={{ x: 20, opacity: 0 }}
									transition={{ delay: idx * 0.1 }}
									className={`p-4 backdrop-blur-sm border rounded-xl transition-all ${priorityStyle} ${
										isUsed ? "opacity-60" : ""
									}`}
								>
									<div className="flex items-start justify-between gap-2 mb-3">
										<div className="flex-1">
											<div className="flex items-center gap-2 mb-1">
												<span className={`text-xs font-bold uppercase ${priorityColor}`}>
													{nudge.priority === "high" && "🔴"}
													{nudge.priority === "medium" && "🟡"}
													{nudge.priority === "low" && "🔵"}
													{" "}{nudge.title}
												</span>
												{isUsed && (
													<CheckCircle className="w-4 h-4 text-green-400" />
												)}
											</div>

											{/* Confidence bar */}
											<div className="flex items-center gap-2 mb-2">
												<span className="text-xs text-slate-400">Confidence</span>
												<div className="flex-1 h-1.5 bg-black/30 rounded-full overflow-hidden">
													<motion.div
														initial={{ width: 0 }}
														animate={{ width: `${nudge.confidence * 100}%` }}
														transition={{ duration: 0.8, ease: "easeOut" }}
														className={`h-full bg-gradient-to-r ${
															nudge.confidence > 0.8
																? "from-emerald-500 to-green-500"
																: nudge.confidence > 0.6
																? "from-yellow-500 to-amber-500"
																: "from-blue-500 to-cyan-500"
														}`}
													/>
												</div>
												<span className="text-xs text-slate-400 font-mono">
													{(nudge.confidence * 100).toFixed(0)}%
												</span>
											</div>

											<p className="text-sm text-slate-200 leading-relaxed mb-3">
												{nudge.suggestion}
											</p>

											{/* Context */}
											<div className="p-2 bg-black/20 rounded-lg border border-white/5">
												<p className="text-xs text-slate-400 italic">
													💬 "{nudge.transcript_chunk}"
												</p>
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

									{/* Actions */}
									<div className="flex items-center gap-2 mt-3">
										{!isUsed ? (
											<button
												onClick={() => handleUse(nudge.id)}
												className="px-3 py-1.5 bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white rounded-lg text-xs font-medium transition-all transform hover:scale-105 shadow-lg"
											>
												✓ Use This
											</button>
										) : (
											<>
												<button
													onClick={() => handleFeedback(nudge.id, true)}
													className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-all flex items-center gap-1"
													title="This helped"
												>
													<ThumbsUp className="w-3 h-3" />
													Helped
												</button>
												<button
													onClick={() => handleFeedback(nudge.id, false)}
													className="px-3 py-1.5 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-xs font-medium transition-all flex items-center gap-1"
													title="Didn't help"
												>
													<ThumbsDown className="w-3 h-3" />
													Not Helpful
												</button>
											</>
										)}
									</div>
								</motion.div>
							);
						})}
					</motion.div>
				)}
			</AnimatePresence>
		</motion.div>
	);
}
