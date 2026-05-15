"use client";

export const dynamic = 'force-dynamic';

import { AudioCapture } from "@/lib/audio-capture";
import { AudioPlayback } from "@/lib/audio-playback";
import { useVoiceCall } from "@/lib/useVoiceCall";
import { NudgePanel } from "@/components/NudgePanel";
import { KBChatPanel } from "@/components/KBChatPanel";
import { ArrowLeft, Globe, Phone, PhoneOff, Mic, MicOff, Volume2, Send, Copy, Check } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

const PRODUCTS = {
	home_loan: "Home Loan",
	personal_loan: "Personal Loan",
	unsecured_loan: "Unsecured Loan",
	loan_against_property: "Loan Against Property",
	gold_loan: "Gold Loan",
	commercial_vehicle_loan: "Commercial Vehicle Loan",
	four_wheeler_loan: "Four Wheeler Loan",
	education_loan: "Education Loan",
	msme_business_loan: "MSME Business Loan",
	credit_card: "Credit Card",
} as const;

const LANGUAGES = [
	{ code: "hi-IN", name: "Hindi", emoji: "🇮🇳" },
	{ code: "en-IN", name: "English", emoji: "🇬🇧" },
	{ code: "ta-IN", name: "Tamil", emoji: "🇮🇳" },
	{ code: "te-IN", name: "Telugu", emoji: "🇮🇳" },
	{ code: "mr-IN", name: "Marathi", emoji: "🇮🇳" },
	{ code: "bn-IN", name: "Bengali", emoji: "🇮🇳" },
	{ code: "gu-IN", name: "Gujarati", emoji: "🇮🇳" },
	{ code: "kn-IN", name: "Kannada", emoji: "🇮🇳" },
	{ code: "ml-IN", name: "Malayalam", emoji: "🇮🇳" },
	{ code: "pa-IN", name: "Punjabi", emoji: "🇮🇳" },
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const E164_PHONE_RE = /^\+[1-9]\d{7,14}$/;

type RealCallStatus = "idle" | "dialing" | "success" | "error";

function normalizePhoneNumber(value: string) {
	const trimmed = value.trim().replace(/[\s().-]+/g, "");
	return trimmed.startsWith("00") ? `+${trimmed.slice(2)}` : trimmed;
}

function extractApiError(payload: unknown, fallback: string) {
	if (payload && typeof payload === "object" && "detail" in payload) {
		const detail = (payload as { detail?: unknown }).detail;
		if (typeof detail === "string") return detail;
		if (Array.isArray(detail)) {
			return detail.map((item) => JSON.stringify(item)).join("; ");
		}
	}
	return fallback;
}

function formatLatencyMs(value: number | undefined) {
	if (typeof value !== "number" || value <= 0) return "N/A";
	return `${value.toFixed(0)}ms`;
}

export default function CallPage() {
	const searchParams = useSearchParams();
	const productParam = searchParams.get("product") || "personal_loan";
	const product = (
		productParam in PRODUCTS ? productParam : "personal_loan"
	) as keyof typeof PRODUCTS;

	const [isInitialized, setIsInitialized] = useState(false);
	const [selectedLanguage, setSelectedLanguage] = useState("hi-IN");
	const [contactInput, setContactInput] = useState("");
	const [customerPhone, setCustomerPhone] = useState("");
	const [realCallStatus, setRealCallStatus] = useState<RealCallStatus>("idle");
	const [realCallMessage, setRealCallMessage] = useState("");
	const [copiedCallId, setCopiedCallId] = useState(false);
	const [customerName, setCustomerName] = useState(
		typeof window !== "undefined" ? localStorage.getItem("customerName") || "" : ""
	);
	const audioCaptureRef = useRef<AudioCapture | null>(null);
	const audioPlaybackRef = useRef<AudioPlayback | null>(null);
	const transcriptEndRef = useRef<HTMLDivElement>(null);

	const callId = useMemo(() => `call_${Date.now()}`, []);

	const voiceCall = useVoiceCall({
		apiBaseUrl: API_BASE_URL,
		callId,
		customerId: "demo_customer",
		product,
		language: selectedLanguage,
		agentName: "Priya",
		lenderName: "Demo Bank",
		customerName: customerName || "Guest",
		onAudioFrame: (pcm) => {
			audioPlaybackRef.current?.enqueue(pcm);
		},
	});

	// Auto-scroll transcript
	useEffect(() => {
		transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [voiceCall.transcript]);

	useEffect(() => {
		if (voiceCall.status === "active" && !isInitialized) {
			const capture = new AudioCapture(voiceCall.sendAudio);
			const playback = new AudioPlayback(16000);

			audioCaptureRef.current = capture;
			audioPlaybackRef.current = playback;
			setIsInitialized(true);

			capture
				.start()
				.catch((err) => console.error("AudioCapture start error:", err));

			playback
				.start()
				.catch((err) => console.error("AudioPlayback start error:", err));
		}

		if (voiceCall.status === "ended") {
			audioCaptureRef.current?.stop();
			audioCaptureRef.current = null;
			audioPlaybackRef.current?.stop();
			audioPlaybackRef.current = null;
		}
	}, [voiceCall.status, voiceCall.sendAudio, isInitialized]);

	const handleStartCall = () => {
		voiceCall.connect();
	};

	const handleEndCall = () => {
		voiceCall.endCall();
	};

	const handleSendContact = () => {
		const text = contactInput.trim();
		if (text) {
			// Clear input immediately to prevent duplicates
			setContactInput("");
			voiceCall.sendText(text);
		}
	};

	const handleCopyCallId = async () => {
		try {
			await navigator.clipboard.writeText(callId);
			setCopiedCallId(true);
			setTimeout(() => setCopiedCallId(false), 2000);
		} catch (err) {
			console.error("Failed to copy:", err);
		}
	};

	const handleRealCall = async () => {
		const normalizedPhone = normalizePhoneNumber(customerPhone);

		if (!normalizedPhone) {
			setRealCallStatus("error");
			setRealCallMessage("Please enter a phone number.");
			return;
		}

		if (!E164_PHONE_RE.test(normalizedPhone)) {
			setRealCallStatus("error");
			setRealCallMessage(
				"Use E.164 format, for example +919876543210. Do not include spaces or a leading local 0.",
			);
			return;
		}

		setRealCallStatus("dialing");
		setRealCallMessage("Requesting Twilio outbound call...");

		try {
			const response = await fetch(`${API_BASE_URL}/call/outbound`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					customer_phone: normalizedPhone,
					product,
					language: selectedLanguage,
					agent_name: "Priya",
					lender_name: "Demo Bank",
					customer_name: "Rahul",
				}),
			});

			const text = await response.text();
			let payload: unknown = {};
			try {
				payload = text ? JSON.parse(text) : {};
			} catch {
				payload = { detail: text };
			}

			if (!response.ok) {
				throw new Error(
					extractApiError(
						payload,
						`API ${response.status}: ${response.statusText}`,
					),
				);
			}

			const data = payload as {
				call_sid?: string;
				call_id?: string;
				to?: string;
			};
			setCustomerPhone(normalizedPhone);
			setRealCallStatus("success");
			setRealCallMessage(
				`Call initiated to ${data.to ?? normalizedPhone}. SID: ${data.call_sid ?? "pending"}`,
			);
		} catch (error) {
			console.error("Error initiating call:", error);
			setRealCallStatus("error");
			setRealCallMessage(
				error instanceof Error ? error.message : "Failed to initiate call.",
			);
		}
	};

	// Check if agent is asking for contact
	const lastAgentMsg = [...voiceCall.transcript]
		.reverse()
		.find(t => t.type === "agent_text");
	const agentText = lastAgentMsg?.text?.toLowerCase() || "";
	const isAskingContact = voiceCall.status === "active" && (
		agentText.includes("email") ||
		agentText.includes("phone") ||
		agentText.includes("whatsapp") ||
		agentText.includes("sms") ||
		agentText.includes("number") ||
		agentText.includes("type kariye")
	);

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 relative overflow-hidden">
			{/* Animated Background */}
			<div className="absolute inset-0 overflow-hidden pointer-events-none">
				<div className="absolute top-1/4 -left-64 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
				<div className="absolute bottom-1/4 -right-64 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
			</div>

			<main className="relative container mx-auto p-6 max-w-6xl">
				{/* Header */}
				<div className="flex items-center justify-between mb-8">
					<div className="flex items-center gap-4">
						<Link
							href="/"
							className="p-3 hover:bg-white/10 rounded-xl transition-all border border-white/10"
						>
							<ArrowLeft className="w-5 h-5 text-white" />
						</Link>
						<div>
							<h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
								{PRODUCTS[product]}
							</h1>
							<p className="text-sm text-slate-400 mt-1">
								AI Voice Assistant Demo
							</p>
						</div>
					</div>

					{/* Language Selector */}
					{voiceCall.status === "idle" && (
						<div className="flex items-center gap-3">
							<Globe className="w-5 h-5 text-slate-400" />
							<select
								value={selectedLanguage}
								onChange={(e) => setSelectedLanguage(e.target.value)}
								className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white text-sm font-medium hover:bg-white/10 focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
							>
								{LANGUAGES.map((lang) => (
									<option key={lang.code} value={lang.code} className="bg-slate-900">
										{lang.emoji} {lang.name}
									</option>
								))}
							</select>
						</div>
					)}
				</div>

				{/* Main Content */}
				<div className="grid lg:grid-cols-3 gap-6">
					{/* Left Column - Call Controls & Info */}
					<div className="lg:col-span-1 space-y-6">
						{/* Call ID Display - Prominent */}
						{voiceCall.status === "active" && (
							<div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
								<div className="flex items-center justify-between gap-3">
									<div>
										<p className="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-1">
											Call ID for Supervisor Monitor
										</p>
										<p className="text-white font-mono text-sm">{callId}</p>
									</div>
									<button
										onClick={handleCopyCallId}
										className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition flex items-center gap-2"
									>
										{copiedCallId ? (
											<>
												<Check className="w-4 h-4" />
												Copied!
											</>
										) : (
											<>
												<Copy className="w-4 h-4" />
												Copy
											</>
										)}
									</button>
								</div>
							</div>
						)}

						{/* Call Control Card */}
						<div className="p-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl">
							{voiceCall.status === "idle" && (
								<div className="text-center space-y-6">
									<div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-2xl shadow-green-500/50">
										<Phone className="w-12 h-12 text-white" />
									</div>
									<div>
										<h3 className="text-xl font-bold text-white mb-2">Ready to Connect</h3>
										<p className="text-sm text-slate-400">
											Start conversation in{" "}
											{LANGUAGES.find((l) => l.code === selectedLanguage)?.name}
										</p>
									</div>

									{/* Real Call Section */}
									<div className="space-y-3 pt-4 border-t border-white/10">
										<h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">Real Phone Call</h4>
										<input
											type="tel"
											placeholder="+919876543210"
											value={customerPhone}
											onChange={(e) => {
												setCustomerPhone(e.target.value);
												setRealCallStatus("idle");
												setRealCallMessage("");
											}}
											className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
										/>
										<button
											onClick={handleRealCall}
											disabled={realCallStatus === "dialing"}
											className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
										>
											<Phone className="w-4 h-4" />
											{realCallStatus === "dialing" ? "Calling..." : "Call Real Number"}
										</button>
										{realCallMessage && (
											<p className={`text-xs ${
												realCallStatus === "error" ? "text-red-400" : "text-green-400"
											}`}>
												{realCallMessage}
											</p>
										)}
										<p className="text-xs text-slate-500">Requires Twilio setup</p>
									</div>

									<div className="pt-4 border-t border-white/10">
										<button
											onClick={handleStartCall}
											className="w-full px-8 py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-xl font-bold shadow-2xl shadow-green-500/50 transition-all transform hover:scale-105"
										>
											Start Browser Demo
										</button>
									</div>
								</div>
							)}

							{voiceCall.status === "connecting" && (
								<div className="text-center space-y-6">
									<div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-2xl shadow-blue-500/50 animate-pulse">
										<Phone className="w-12 h-12 text-white animate-bounce" />
									</div>
									<div>
										<h3 className="text-xl font-bold text-white mb-2">Connecting...</h3>
										<p className="text-sm text-slate-400">
											Establishing secure connection
										</p>
									</div>
								</div>
							)}

							{voiceCall.status === "active" && (
								<div className="text-center space-y-6">
									<div className="relative">
										<div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-red-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-red-500/50">
											<Mic className="w-12 h-12 text-white" />
										</div>
										{/* Pulse animation */}
										<div className="absolute inset-0 w-24 h-24 mx-auto rounded-full bg-red-500/20 animate-ping" />
									</div>
									<div>
										<h3 className="text-xl font-bold text-white mb-2">Call in Progress</h3>
										<div className="flex items-center justify-center gap-2">
											<div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
											<p className="text-sm text-slate-400">Recording</p>
										</div>
									</div>
									<button
										onClick={handleEndCall}
										className="w-full px-8 py-4 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white rounded-xl font-bold shadow-2xl shadow-red-500/50 transition-all transform hover:scale-105"
									>
										End Call
									</button>
								</div>
							)}
						</div>

						{/* Call Stats - Active Call */}
						{voiceCall.status === "active" && (
							<div className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl space-y-4">
								<h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">Call Metrics</h4>
								<div className="grid grid-cols-2 gap-4">
									<div>
										<p className="text-xs text-slate-500 mb-1">Turns</p>
										<p className="text-2xl font-bold text-white">{voiceCall.metrics.turn_count}</p>
									</div>
									<div>
										<p className="text-xs text-slate-500 mb-1">Duration</p>
										<p className="text-2xl font-bold text-white">
											{voiceCall.metrics.duration_s.toFixed(0)}s
										</p>
									</div>
								</div>
							</div>
						)}

						{/* Call Info - Active Call */}
						{voiceCall.status === "active" && (
							<div className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl space-y-3">
								<h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">Session Info</h4>
								<div className="space-y-2 text-xs">
									<div className="flex justify-between">
										<span className="text-slate-500">Call ID</span>
										<span className="text-white font-medium font-mono">{callId}</span>
									</div>
									<div className="flex justify-between">
										<span className="text-slate-500">Product</span>
										<span className="text-white font-medium">{PRODUCTS[product]}</span>
									</div>
									<div className="flex justify-between">
										<span className="text-slate-500">Agent</span>
										<span className="text-white font-medium">Priya</span>
									</div>
									<div className="flex justify-between">
										<span className="text-slate-500">Customer</span>
										<span className="text-white font-medium">
											{customerName || "Guest"}
										</span>
									</div>
									<div className="flex justify-between">
										<span className="text-slate-500">Language</span>
										<span className="text-white font-medium">
											{LANGUAGES.find((l) => l.code === selectedLanguage)?.name}
										</span>
									</div>
								</div>
							</div>
						)}
n							{/* Nudge Panel - Active Call */}
							{voiceCall.status === "active" && (
								<NudgePanel
									callId={callId}
									product={product}
									apiBaseUrl={API_BASE_URL}
								/>
							)}
					</div>

					{/* Right Column - Transcript */}
					<div className="lg:col-span-2">
						<div className="h-[calc(100vh-12rem)] bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden flex flex-col">
							{/* Transcript Header */}
							<div className="px-6 py-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
								<div className="flex items-center gap-3">
									<Volume2 className="w-5 h-5 text-blue-400" />
									<h2 className="text-lg font-semibold text-white">Live Transcript</h2>
								</div>
								{voiceCall.status === "active" && (
									<div className="flex items-center gap-2">
										<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
										<span className="text-xs text-slate-400">Recording</span>
									</div>
								)}
							</div>

							{/* Transcript Content */}
							<div className="flex-1 overflow-y-auto p-6 space-y-4">
								{voiceCall.transcript.length === 0 && voiceCall.status === "idle" && (
									<div className="h-full flex items-center justify-center text-center">
										<div>
											<Phone className="w-16 h-16 text-slate-600 mx-auto mb-4" />
											<p className="text-slate-400">Click "Start Call" to begin conversation</p>
										</div>
									</div>
								)}

								{voiceCall.transcript.length === 0 && voiceCall.status === "connecting" && (
									<div className="h-full flex items-center justify-center text-center">
										<div>
											<div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
											<p className="text-slate-400">Connecting to agent...</p>
										</div>
									</div>
								)}

								{/* Chat Messages */}
								{voiceCall.transcript.map((item, idx) => (
									<div
										key={idx}
										className={`flex ${item.type === "agent_text" ? "justify-start" : "justify-end"}`}
									>
										<div
											className={`max-w-[80%] px-4 py-3 rounded-2xl ${
												item.type === "agent_text"
													? "bg-blue-500/20 border border-blue-500/30 text-white"
													: item.type === "asr_partial"
													? "bg-white/5 border border-white/10 text-slate-400 italic"
													: "bg-green-500/20 border border-green-500/30 text-white"
											}`}
										>
											<div className="flex items-start gap-2">
												{item.type === "agent_text" && (
													<span className="text-xs text-blue-400 font-semibold">Agent</span>
												)}
												{item.type !== "agent_text" && (
													<span className="text-xs text-green-400 font-semibold">You</span>
												)}
											</div>
											<p className="mt-1 text-sm leading-relaxed">{item.text}</p>
										</div>
									</div>
								))}

								<div ref={transcriptEndRef} />
							</div>

							{/* Contact Input - Conditional */}
							{isAskingContact && (
								<div className="p-4 bg-amber-500/10 border-t border-amber-500/30">
									<div className="flex items-center gap-2 mb-2">
										<span className="text-xs font-semibold text-amber-400 uppercase">📝 Type Contact Info</span>
									</div>
									<div className="flex gap-2">
										<input
											type="text"
											value={contactInput}
											onChange={(e) => setContactInput(e.target.value)}
											onKeyPress={(e) => {
												if (e.key === "Enter") {
													e.preventDefault();
													handleSendContact();
												}
											}}
											placeholder="e.g. user@email.com or +919876543210"
											className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-amber-500 focus:border-transparent"
										/>
										<button
											onClick={handleSendContact}
											className="px-6 py-3 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl font-medium transition-all transform hover:scale-105"
										>
											<Send className="w-5 h-5" />
										</button>
									</div>
									<p className="text-xs text-amber-400 mt-2">
										⚠️ Type here to avoid mishearing. Press Enter or click Send.
									</p>
								</div>
							)}
						</div>
					</div>
				</div>

				{/* Call Summary - After Ended */}
				{voiceCall.status === "ended" && (
					<div className="mt-6 p-8 bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-sm border border-white/20 rounded-2xl">
						<h2 className="text-3xl font-bold text-white mb-6">Call Summary</h2>

						<div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
							<div className="text-center p-4 bg-white/5 rounded-xl">
								<p className="text-sm text-slate-400 mb-2">Total Turns</p>
								<p className="text-4xl font-bold text-white">{voiceCall.metrics.turn_count}</p>
							</div>
							<div className="text-center p-4 bg-white/5 rounded-xl">
								<p className="text-sm text-slate-400 mb-2">Duration</p>
								<p className="text-4xl font-bold text-white">
									{voiceCall.metrics.duration_s.toFixed(1)}s
								</p>
							</div>
							<div className="text-center p-4 bg-white/5 rounded-xl">
								<p className="text-sm text-slate-400 mb-2">ASR Latency</p>
								<p className="text-2xl font-bold text-white">
									{formatLatencyMs(voiceCall.metrics.last_latency?.asr_ms)}
								</p>
							</div>
							<div className="text-center p-4 bg-white/5 rounded-xl">
								<p className="text-sm text-slate-400 mb-2">LLM Latency</p>
								<p className="text-2xl font-bold text-white">
									{formatLatencyMs(voiceCall.metrics.last_latency?.llm_ms)}
								</p>
							</div>
						</div>

						{voiceCall.metrics.last_latency && (
							<div className="mb-8 p-6 bg-white/5 rounded-xl">
								<h3 className="text-lg font-semibold text-slate-300 mb-4">
									Performance Breakdown
								</h3>
								<div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
									<div>
										<p className="text-slate-400 mb-1">ASR</p>
										<p className="text-xl font-semibold text-white">
											{formatLatencyMs(voiceCall.metrics.last_latency.asr_ms)}
										</p>
									</div>
									<div>
										<p className="text-slate-400 mb-1">LLM</p>
										<p className="text-xl font-semibold text-white">
											{formatLatencyMs(voiceCall.metrics.last_latency.llm_ms)}
										</p>
									</div>
									<div>
										<p className="text-slate-400 mb-1">TTS First Byte</p>
										<p className="text-xl font-semibold text-white">
											{formatLatencyMs(voiceCall.metrics.last_latency.tts_first_byte_ms)}
										</p>
									</div>
									<div>
										<p className="text-slate-400 mb-1">End-to-End</p>
										<p className="text-xl font-semibold text-white">
											{formatLatencyMs(voiceCall.metrics.last_latency.e2e_ms)}
										</p>
									</div>
								</div>
							</div>
						)}

						<div className="flex gap-4">
							<button
								onClick={() => window.location.reload()}
								className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-xl font-semibold transition-all"
							>
								Start New Call
							</button>
							<Link
								href="/"
								className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl font-semibold transition-all text-center"
							>
								Back to Home
							</Link>
						</div>
					</div>
				)}

				{/* Error Display */}
				{voiceCall.error && (
					<div className="mt-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
						<p className="text-sm text-red-400 font-medium">
							Error: {voiceCall.error}
						</p>
					</div>
				)}
			</main>

			{/* KB Chat Panel - available always */}
			<KBChatPanel callId={undefined} />
		</div>
	);
}
