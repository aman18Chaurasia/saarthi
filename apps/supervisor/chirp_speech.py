"""Google Cloud Speech Chirp-3 integration for diarization and transcription.

Chirp-3 supports English, Hindi, and Hinglish with speaker separation.
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path

from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


@dataclass
class TranscriptSegment:
    """Transcribed segment with speaker label."""

    speaker: str  # "agent" or "customer"
    text: str
    start_time: float
    end_time: float
    confidence: float


class ChirpSpeechDiarizer:
    """Real-time speech diarization and transcription using Google Chirp-3."""

    def __init__(self):
        """Initialize Google Cloud Speech client."""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable required")

        # Load project_id from credentials file
        with open(credentials_path) as f:
            creds = json.load(f)
            self.project_id = creds["project_id"]

        # Create Speech client
        self.client = SpeechClient()

        # Recognizer resource name for Chirp-3
        # Format: projects/{project}/locations/{location}/recognizers/{recognizer}
        # Use 'chirp' recognizer for Chirp-3 model
        self.location = os.getenv("GOOGLE_SPEECH_LOCATION", "us")
        self.recognizer_path = f"projects/{self.project_id}/locations/{self.location}/recognizers/_"

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
        loop = asyncio.get_event_loop()

        def generate_requests():
            """Generate streaming requests."""
            # First request - config
            config = cloud_speech.StreamingRecognitionConfig(
                config=cloud_speech.RecognitionConfig(
                    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
                    language_codes=["en-IN", "hi-IN"],  # English (India) and Hindi for Hinglish
                    model="chirp_3",  # Chirp-3 model
                    features=cloud_speech.RecognitionFeatures(
                        enable_automatic_punctuation=True,
                        enable_word_time_offsets=True,
                        diarization_config=cloud_speech.SpeakerDiarizationConfig(
                            min_speaker_count=2,
                            max_speaker_count=2,
                        ),
                    ),
                ),
                streaming_features=cloud_speech.StreamingRecognitionFeatures(
                    interim_results=True,
                ),
            )

            yield cloud_speech.StreamingRecognizeRequest(
                recognizer=self.recognizer_path,
                streaming_config=config,
            )

            # Audio chunks
            try:
                while True:
                    chunk = audio_stream.get_nowait()
                    if chunk is None:
                        break
                    yield cloud_speech.StreamingRecognizeRequest(audio=chunk)
            except asyncio.QueueEmpty:
                pass

        def process_responses():
            """Process streaming responses."""
            responses = self.client.streaming_recognize(requests=generate_requests())

            speaker_map = {}  # Map speaker tags to agent/customer

            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                alternative = result.alternatives[0]
                text = alternative.transcript

                if not text.strip():
                    continue

                # Extract speaker diarization info
                if alternative.words:
                    # Get speaker tag from first word
                    speaker_tag = alternative.words[0].speaker_label if hasattr(alternative.words[0], "speaker_label") else None

                    if speaker_tag:
                        # Map speaker tag to agent/customer
                        # First speaker = agent, second = customer
                        if speaker_tag not in speaker_map:
                            speaker_label = "agent" if len(speaker_map) == 0 else "customer"
                            speaker_map[speaker_tag] = speaker_label
                        speaker = speaker_map[speaker_tag]
                    else:
                        speaker = "agent"  # Default

                    # Calculate time bounds
                    start_time = alternative.words[0].start_offset.total_seconds()
                    end_time = alternative.words[-1].end_offset.total_seconds()
                else:
                    speaker = "agent"
                    start_time = 0.0
                    end_time = 0.0

                # Only emit final results
                if result.is_final:
                    segment = TranscriptSegment(
                        speaker=speaker,
                        text=text,
                        start_time=start_time,
                        end_time=end_time,
                        confidence=alternative.confidence,
                    )

                    # Put in queue (thread-safe)
                    asyncio.run_coroutine_threadsafe(
                        result_queue.put(segment),
                        loop
                    )

        # Run blocking speech recognition in thread pool
        await loop.run_in_executor(None, process_responses)


async def test_chirp_speech():
    """Test Google Chirp-3 diarization."""
    diarizer = ChirpSpeechDiarizer()

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
    asyncio.run(test_chirp_speech())
