"""Azure Speech Services integration for diarization and transcription.

Supports English and Hinglish with speaker separation.
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass

import azure.cognitiveservices.speech as speechsdk


@dataclass
class TranscriptSegment:
    """Transcribed segment with speaker label."""

    speaker: str  # "agent" or "customer"
    text: str
    start_time: float
    end_time: float
    confidence: float


class AzureSpeechDiarizer:
    """Real-time speech diarization and transcription using Azure."""

    def __init__(self):
        """Initialize Azure Speech SDK."""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus")

        if not self.speech_key:
            raise ValueError("AZURE_SPEECH_KEY environment variable required")

        # Speech config with conversation transcription
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region,
        )

        # Enable diarization
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EnableAudioLogging,
            "false",  # Privacy: don't log audio to Azure
        )

        # Support English and Hindi
        self.speech_config.speech_recognition_language = "en-IN"  # English (India) - supports Hinglish

    async def transcribe_stream(
        self,
        audio_stream: asyncio.Queue[bytes],
        result_queue: asyncio.Queue[TranscriptSegment],
    ) -> None:
        """Transcribe audio stream with speaker diarization.

        Args:
            audio_stream: Queue of PCM int16 mono 16kHz audio chunks
            result_queue: Queue to put transcript segments into
        """
        # Create push stream
        stream = speechsdk.audio.PushAudioInputStream()

        # Audio config from stream
        audio_config = speechsdk.audio.AudioConfig(stream=stream)

        # Conversation transcriber (enables diarization)
        transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        # Results storage
        segments: list[TranscriptSegment] = []
        done = asyncio.Event()
        loop = asyncio.get_event_loop()

        def transcribed_cb(evt):
            """Handle transcription result (runs in SDK thread)."""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Extract speaker ID and text
                speaker_id = evt.result.speaker_id or "Unknown"
                text = evt.result.text

                if text.strip():
                    # Map speaker_id to agent/customer
                    # Guest-1 = first speaker (usually agent)
                    # Guest-2 = second speaker (usually customer)
                    speaker = "agent" if speaker_id == "Guest-1" else "customer"

                    segment = TranscriptSegment(
                        speaker=speaker,
                        text=text,
                        start_time=evt.result.offset / 10_000_000,  # Convert to seconds
                        end_time=(evt.result.offset + evt.result.duration) / 10_000_000,
                        confidence=evt.result.confidence if hasattr(evt.result, "confidence") else 1.0,
                    )

                    segments.append(segment)

                    # Put in queue (thread-safe)
                    asyncio.run_coroutine_threadsafe(
                        result_queue.put(segment),
                        loop
                    )

        def canceled_cb(evt):
            """Handle cancellation."""
            if evt.reason == speechsdk.CancellationReason.Error:
                print(f"[Azure] Error: {evt.error_details}")
            done.set()

        def stopped_cb(evt):
            """Handle stop."""
            done.set()

        # Connect callbacks
        transcriber.transcribed.connect(transcribed_cb)
        transcriber.canceled.connect(canceled_cb)
        transcriber.session_stopped.connect(stopped_cb)

        # Start transcription
        transcriber.start_transcribing_async().get()

        # Feed audio chunks
        try:
            while True:
                chunk = await audio_stream.get()

                if chunk is None:  # Sentinel value to stop
                    break

                # Write to push stream
                stream.write(chunk)

        finally:
            # Stop transcription
            stream.close()
            transcriber.stop_transcribing_async().get()


async def test_azure_speech():
    """Test Azure Speech diarization."""
    diarizer = AzureSpeechDiarizer()

    audio_queue = asyncio.Queue()
    result_queue = asyncio.Queue()

    # Simulate audio input
    async def feed_audio():
        # Read test audio file
        import wave

        with wave.open("test.wav", "rb") as wav:
            while chunk := wav.readframes(4096):
                await audio_queue.put(chunk)
                await asyncio.sleep(0.1)

        await audio_queue.put(None)  # Signal end

    # Print results
    async def print_results():
        while True:
            seg = await result_queue.get()
            if seg is None:
                break
            print(f"[{seg.speaker}] {seg.text}")

    await asyncio.gather(
        feed_audio(),
        diarizer.transcribe_stream(audio_queue, result_queue),
        print_results(),
    )


if __name__ == "__main__":
    asyncio.run(test_azure_speech())
