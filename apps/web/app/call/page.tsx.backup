"use client";

import { AudioCapture } from "@/lib/audio-capture";
import { AudioPlayback } from "@/lib/audio-playback";
import { useVoiceCall } from "@/lib/useVoiceCall";
import { ArrowLeft, Globe, Phone, PhoneOff } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Transcript } from "./transcript";

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
		if (typeof detail === "string") {
			return detail;
		}
		if (Array.isArray(detail)) {
			return detail.map((item) => JSON.stringify(item)).join("; ");
		}
	}
	return fallback;
}

function formatLatencyMs(value: number | undefined) {
	if (typeof value !== "number" || value <= 0) {
		return "N/A";
	}
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
	const [customerPhone, setCustomerPhone] = useState("");
	const [realCallStatus, setRealCallStatus] = useState<RealCallStatus>("idle");
	const [realCallMessage, setRealCallMessage] = useState("");
	const audioCaptureRef = useRef<AudioCapture | null>(null);
	const audioPlaybackRef = useRef<AudioPlayback | null>(null);

	const callId = useMemo(() => `call_${Date.now()}`, []);

	const voiceCall = useVoiceCall({
		apiBaseUrl: API_BASE_URL,
		callId,
		customerId: "demo_customer",
		product,
		language: selectedLanguage,
		agentName: "Priya",
		lenderName: "Demo Bank",
		customerName: "Rahul",
		onAudioFrame: (pcm) => {
			audioPlaybackRef.current?.enqueue(pcm);
		},
	});

	useEffect(() => {
		if (voiceCall.status === "active" && !isInitialized) {
			setIsInitialized(true);

			// Start mic capture
			audioCaptureRef.current = new AudioCapture((pcm) => {
				voiceCall.sendAudio(pcm);
			});
			audioCaptureRef.current.start().catch(console.error);
		}

		if (voiceCall.status === "ended" && isInitialized) {
			audioCaptureRef.current?.stop();
			audioPlaybackRef.current?.stop();
			setIsInitialized(false);
		}
	}, [voiceCall.status, voiceCall.sendAudio, isInitialized]);

	useEffect(() => {
		return () => {
			audioCaptureRef.current?.stop();
			audioPlaybackRef.current?.stop();
		};
	}, []);

	const handleStartCall = async () => {
		// Start audio playback
		audioPlaybackRef.current = new AudioPlayback();
		await audioPlaybackRef.current.start();

		voiceCall.connect();
	};

	const handleEndCall = () => {
		audioCaptureRef.current?.stop();
		audioPlaybackRef.current?.stop();
		voiceCall.endCall();
		setIsInitialized(false);
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

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
			<main className="container mx-auto p-6 max-w-5xl">
				<div className="flex flex-col gap-6">
					{/* Header */}
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-4">
							<Link
								href="/"
								className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
							>
								<ArrowLeft className="w-5 h-5" />
							</Link>
							<div>
								<h1 className="text-3xl font-bold text-slate-900">
									{PRODUCTS[product]}
								</h1>
								<p className="text-sm text-slate-600 mt-1">
									AI Voice Assistant Demo
								</p>
							</div>
						</div>

						{/* Language Selector */}
						{voiceCall.status === "idle" && (
							<div className="flex items-center gap-3">
								<Globe className="w-5 h-5 text-slate-500" />
								<select
									value={selectedLanguage}
									onChange={(e) => setSelectedLanguage(e.target.value)}
									className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium bg-white hover:bg-slate-50 focus:ring-2 focus:ring-primary focus:border-transparent"
								>
									{LANGUAGES.map((lang) => (
										<option key={lang.code} value={lang.code}>
											{lang.emoji} {lang.name}
										</option>
									))}
								</select>
							</div>
						)}
					</div>

					{/* Call Controls */}
					<div className="flex flex-col gap-4 justify-center items-center">
						{voiceCall.status === "idle" && (
							<>
								{/* Real Call Section */}
								<div className="flex flex-col gap-3 items-center p-6 bg-white rounded-xl shadow-lg border border-slate-200">
									<h3 className="text-lg font-semibold text-slate-900">
										Make Real Call
									</h3>
									<div className="flex flex-col sm:flex-row gap-3 w-full">
										<input
											type="tel"
											placeholder="+919876543210"
											value={customerPhone}
											onChange={(e) => {
												setCustomerPhone(e.target.value);
												setRealCallStatus("idle");
												setRealCallMessage("");
											}}
											className="px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
										/>
										<button
											type="button"
											onClick={handleRealCall}
											disabled={realCallStatus === "dialing"}
											className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed font-semibold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
										>
											<Phone className="w-4 h-4" />
											{realCallStatus === "dialing"
												? "Calling..."
												: "Call Real Number"}
										</button>
									</div>
									{realCallMessage && (
										<p
											className={`text-xs text-center max-w-xl ${
												realCallStatus === "error"
													? "text-red-700"
													: "text-green-700"
											}`}
										>
											{realCallMessage}
										</p>
									)}
									<p className="text-xs text-slate-500 text-center">
										Requires Twilio setup. Uses real phone numbers.
									</p>
								</div>

								{/* Browser Demo Call */}
								<div className="flex gap-3">
									<button
										type="button"
										onClick={handleStartCall}
										className="group px-8 py-4 bg-green-600 text-white rounded-xl hover:bg-green-700 font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-3"
									>
										<Phone className="w-5 h-5" />
										Start Call in{" "}
										{LANGUAGES.find((l) => l.code === selectedLanguage)?.name}
									</button>
								</div>
							</>
						)}

						{voiceCall.status === "connecting" && (
							<button
								type="button"
								disabled
								className="px-8 py-4 bg-slate-300 text-slate-600 rounded-xl cursor-not-allowed font-semibold flex items-center gap-3"
							>
								<div className="w-5 h-5 border-2 border-slate-600 border-t-transparent rounded-full animate-spin" />
								Connecting...
							</button>
						)}

						{voiceCall.status === "active" && (
							<button
								type="button"
								onClick={handleEndCall}
								className="px-8 py-4 bg-red-600 text-white rounded-xl hover:bg-red-700 font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-3"
							>
								<PhoneOff className="w-5 h-5" />
								End Call
							</button>
						)}
					</div>

					{/* Error Display */}
					{voiceCall.error && (
						<div className="p-4 bg-red-50 border border-red-200 rounded-xl">
							<p className="text-sm text-red-700 font-medium">
								Error: {voiceCall.error}
							</p>
						</div>
					)}

					{/* Transcript Section */}
					<div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
						<div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
							<h2 className="text-lg font-semibold text-slate-900">
								Live Transcript
							</h2>
							{voiceCall.status === "active" && (
								<div className="flex items-center gap-2">
									<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
									<span className="text-sm text-slate-600">Recording</span>
								</div>
							)}
						</div>

						<div className="p-6">
							{voiceCall.transcript.length === 0 &&
								voiceCall.status === "idle" && (
									<p className="text-center text-slate-500 py-12">
										Click "Start Call" to begin conversation
									</p>
								)}
							{voiceCall.transcript.length === 0 &&
								voiceCall.status === "connecting" && (
									<p className="text-center text-slate-500 py-12">
										Connecting to agent...
									</p>
								)}
							<Transcript items={voiceCall.transcript} />

							{/* Text Input for Contact Info - Show only when agent asks */}
							{voiceCall.status === "active" && (() => {
								// Show input box only when agent asks for contact info
								const lastAgentMsg = [...voiceCall.transcript]
									.reverse()
									.find(t => t.type === "agent_text");
								const agentText = lastAgentMsg?.text?.toLowerCase() || "";
								const isAskingContact =
									agentText.includes("email") ||
									agentText.includes("phone") ||
									agentText.includes("whatsapp") ||
									agentText.includes("sms") ||
									agentText.includes("number") ||
									agentText.includes("type kariye");

								return isAskingContact ? (
									<div className="mt-6 pt-6 border-t border-slate-200 bg-amber-50 rounded-lg p-4">
										<label className="block text-sm font-medium text-slate-700 mb-2">
											📝 Type Contact Info (Don't speak this)
										</label>
										<div className="flex gap-2">
											<input
												type="text"
												placeholder="e.g. user@email.com or +919876543210"
												className="flex-1 px-4 py-2 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
												onKeyPress={(e) => {
													if (e.key === "Enter" && e.currentTarget.value.trim()) {
														voiceCall.sendText(e.currentTarget.value.trim());
														e.currentTarget.value = "";
													}
												}}
											/>
											<button
												type="button"
												className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-medium"
												onClick={(e) => {
													const input = e.currentTarget.previousElementSibling as HTMLInputElement;
													if (input.value.trim()) {
														voiceCall.sendText(input.value.trim());
														input.value = "";
													}
												}}
											>
												Send
											</button>
										</div>
										<p className="text-xs text-amber-700 mt-2 font-medium">
											⚠️ Type here to avoid mishearing. Press Enter or click Send.
										</p>
									</div>
								) : null;
							})()}
						</div>
					</div>

					{/* Call Summary (After Call Ends) */}
					{voiceCall.status === "ended" && (
						<div className="bg-gradient-to-br from-slate-800 to-slate-900 text-white rounded-xl shadow-xl p-8">
							<h2 className="text-2xl font-bold mb-6">Call Summary</h2>

							<div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
								<div className="text-center">
									<p className="text-sm text-slate-400 mb-2">Total Turns</p>
									<p className="text-3xl font-bold">
										{voiceCall.metrics.turn_count}
									</p>
								</div>

								<div className="text-center">
									<p className="text-sm text-slate-400 mb-2">Duration</p>
									<p className="text-3xl font-bold">
										{voiceCall.metrics.duration_s.toFixed(1)}s
									</p>
								</div>

								{voiceCall.metrics.last_latency && (
									<>
										<div className="text-center">
											<p className="text-sm text-slate-400 mb-2">Avg Latency</p>
											<p className="text-2xl font-bold">
												{formatLatencyMs(voiceCall.metrics.last_latency.e2e_ms)}
											</p>
										</div>

										<div className="text-center">
											<p className="text-sm text-slate-400 mb-2">LLM Time</p>
											<p className="text-2xl font-bold">
												{formatLatencyMs(voiceCall.metrics.last_latency.llm_ms)}
											</p>
										</div>
									</>
								)}
							</div>

							{voiceCall.metrics.last_latency && (
								<div className="bg-slate-700/50 rounded-lg p-6 mb-6">
									<h3 className="text-sm font-semibold text-slate-300 mb-4">
										Performance Breakdown
									</h3>
									<div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
										<div>
											<p className="text-slate-400">ASR</p>
											<p className="text-lg font-semibold">
												{formatLatencyMs(voiceCall.metrics.last_latency.asr_ms)}
											</p>
										</div>
										<div>
											<p className="text-slate-400">LLM</p>
											<p className="text-lg font-semibold">
												{formatLatencyMs(voiceCall.metrics.last_latency.llm_ms)}
											</p>
										</div>
										<div>
											<p className="text-slate-400">TTS First Byte</p>
											<p className="text-lg font-semibold">
												{formatLatencyMs(
													voiceCall.metrics.last_latency.tts_first_byte_ms,
												)}
											</p>
										</div>
										<div>
											<p className="text-slate-400">End-to-End</p>
											<p className="text-lg font-semibold">
												{formatLatencyMs(voiceCall.metrics.last_latency.e2e_ms)}
											</p>
										</div>
									</div>
								</div>
							)}

							<div className="flex gap-4">
								<button
									type="button"
									onClick={() => window.location.reload()}
									className="flex-1 px-6 py-3 bg-white text-slate-900 rounded-lg hover:bg-slate-100 font-semibold transition-colors"
								>
									Start New Call
								</button>
								<Link
									href="/"
									className="flex-1 px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 font-semibold transition-colors text-center"
								>
									Back to Home
								</Link>
							</div>
						</div>
					)}

					{/* Call Info */}
					{voiceCall.status === "active" && (
						<div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
							<div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-600">
								<div>
									<span className="font-semibold">Call ID:</span> {callId}
								</div>
								<div>
									<span className="font-semibold">Product:</span>{" "}
									{PRODUCTS[product]}
								</div>
								<div>
									<span className="font-semibold">Language:</span>{" "}
									{LANGUAGES.find((l) => l.code === selectedLanguage)?.name}
								</div>
								<div>
									<span className="font-semibold">Customer:</span> Rahul
								</div>
								<div>
									<span className="font-semibold">Agent:</span> Priya
								</div>
							</div>
						</div>
					)}
				</div>
			</main>
		</div>
	);
}
