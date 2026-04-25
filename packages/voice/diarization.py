"""Speaker diarization for real-time audio streams.

Separates agent vs customer audio using pyannote.audio.
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pyannote.audio import Pipeline


@dataclass
class SpeakerSegment:
    """Single speaker segment with audio and metadata."""

    speaker: str  # "SPEAKER_00" or "SPEAKER_01"
    audio: bytes  # PCM int16 mono 16kHz
    start: float  # seconds
    end: float  # seconds


class SpeakerDiarizer:
    """Real-time speaker diarization processor."""

    def __init__(self, model_name: str = "pyannote/speaker-diarization-3.1"):
        """Initialize diarization pipeline.

        Args:
            model_name: HuggingFace model name. Requires HF_TOKEN env var.
        """
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable required for pyannote.audio")

        self.pipeline = Pipeline.from_pretrained(model_name, use_auth_token=hf_token)

    def process_chunk(
        self,
        audio_pcm: bytes,
        sample_rate: int = 16000,
        num_speakers: int = 2,
    ) -> list[SpeakerSegment]:
        """Process audio chunk and return speaker segments.

        Args:
            audio_pcm: Raw PCM int16 mono audio bytes
            sample_rate: Audio sample rate (default 16kHz)
            num_speakers: Expected number of speakers (agent + customer = 2)

        Returns:
            List of speaker segments with labeled audio
        """
        # Convert PCM bytes to numpy array
        audio_array = np.frombuffer(audio_pcm, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0

        # Create in-memory audio file
        from pydub import AudioSegment

        audio_segment = AudioSegment(
            audio_float.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1,
        )

        # Save to temporary wav
        temp_path = Path("/tmp") / f"diarize_{os.getpid()}.wav"
        audio_segment.export(temp_path, format="wav")

        try:
            # Run diarization
            diarization = self.pipeline(
                str(temp_path),
                num_speakers=num_speakers,
            )

            # Extract segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start_sample = int(turn.start * sample_rate)
                end_sample = int(turn.end * sample_rate)

                segment_audio = audio_array[start_sample:end_sample].tobytes()

                segments.append(
                    SpeakerSegment(
                        speaker=speaker,
                        audio=segment_audio,
                        start=turn.start,
                        end=turn.end,
                    )
                )

            return segments

        finally:
            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink()

    def label_speakers(
        self,
        segments: list[SpeakerSegment],
        agent_speaker_id: str | None = None,
    ) -> list[SpeakerSegment]:
        """Relabel speakers as 'agent' or 'customer'.

        Args:
            segments: Raw segments with SPEAKER_XX labels
            agent_speaker_id: If known, which speaker is agent (e.g. "SPEAKER_00")

        Returns:
            Segments with 'agent' or 'customer' labels
        """
        if not agent_speaker_id:
            # Heuristic: first speaker is usually agent (they open call)
            agent_speaker_id = segments[0].speaker if segments else "SPEAKER_00"

        relabeled = []
        for seg in segments:
            new_label = "agent" if seg.speaker == agent_speaker_id else "customer"
            relabeled.append(
                SpeakerSegment(
                    speaker=new_label,
                    audio=seg.audio,
                    start=seg.start,
                    end=seg.end,
                )
            )

        return relabeled
