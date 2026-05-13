"""WebSocket endpoints for supervisor transcription and nudge feed."""
from __future__ import annotations

import asyncio
import json
import os

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


@router.websocket("/feed/{call_id}")
async def supervisor_feed(websocket: WebSocket, call_id: str):
    """Stream transcript and nudges to supervisor UI.

    Subscribes to:
    - supervisor:{call_id}:transcript
    - supervisor:{call_id}:nudges

    Sends JSON messages:
    - {"type": "transcript", "speaker": "agent|customer", "text": "...", "timestamp": ...}
    - {"type": "nudge", "route": "...", "title": "...", "suggestion": "...", ...}
    """
    await websocket.accept()

    r = await redis.from_url(REDIS_URL)
    pubsub = r.pubsub()

    try:
        # Subscribe to transcript and nudge streams
        await pubsub.subscribe(
            f"supervisor:{call_id}:transcript",
            f"supervisor:{call_id}:nudges",
        )

        # Listen and forward to WebSocket
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Forward raw message to UI
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                await websocket.send_text(data)

    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
        await r.close()


@router.websocket("/ingress/{call_id}")
async def audio_ingress(websocket: WebSocket, call_id: str):
    """Receive audio chunks for diarization and transcription.

    This endpoint receives raw audio from call system and:
    1. Diarizes to separate speakers
    2. Transcribes each speaker segment
    3. Publishes to transcript stream

    Audio format: PCM int16 mono 16kHz
    """
    await websocket.accept()

    # Lazy imports (heavy dependencies)
    from voice.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer()
    r = await redis.from_url(REDIS_URL)

    audio_buffer = bytearray()
    CHUNK_SIZE = 32000  # 2 seconds at 16kHz

    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)

            # Process every 2 seconds
            if len(audio_buffer) >= CHUNK_SIZE:
                chunk_bytes = bytes(audio_buffer[:CHUNK_SIZE])
                audio_buffer = audio_buffer[CHUNK_SIZE:]

                # Diarize
                segments = diarizer.process_chunk(chunk_bytes)
                segments = diarizer.label_speakers(segments)

                # Transcribe each segment
                for seg in segments:
                    # Use Groq Whisper for transcription
                    text = await _transcribe_audio(seg.audio)

                    if text.strip():
                        # Publish transcript chunk
                        chunk = {
                            "type": "transcript",
                            "call_id": call_id,
                            "speaker": seg.speaker,
                            "text": text,
                            "start_time": seg.start,
                            "end_time": seg.end,
                            "timestamp": seg.end,
                        }

                        # Publish to transcript stream
                        await r.publish(
                            f"supervisor:{call_id}:transcript",
                            json.dumps(chunk),
                        )

                        # Add to processing queue for nudge worker
                        await r.xadd(
                            f"supervisor:{call_id}:chunks",
                            {"data": json.dumps(chunk)},
                        )

    except WebSocketDisconnect:
        pass
    finally:
        await r.close()


async def _transcribe_audio(audio_pcm: bytes) -> str:
    """Transcribe audio using Groq Whisper API.

    Args:
        audio_pcm: PCM int16 mono 16kHz audio bytes

    Returns:
        Transcribed text
    """
    import tempfile
    from pathlib import Path

    # Convert PCM to wav file for Whisper API
    from pydub import AudioSegment
    import numpy as np

    audio_array = np.frombuffer(audio_pcm, dtype=np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=16000,
        sample_width=2,
        channels=1,
    )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = Path(f.name)
        audio_segment.export(temp_path, format="wav")

    try:
        # Transcribe using Groq Whisper API
        import httpx

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable required")

        async with httpx.AsyncClient() as client:
            with open(temp_path, "rb") as audio_file:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_api_key}"},
                    files={"file": audio_file},
                    data={"model": "whisper-large-v3"},
                )
                resp.raise_for_status()
                text = resp.json()["text"]

        return text

    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.websocket("/monitored/{call_id}")
async def monitored_call(websocket: WebSocket, call_id: str):
    """Real-time monitored call with Google Chirp-3 diarization.

    Receives audio from browser → Chirp-3 transcription → nudge pipeline → sends back
    transcript + nudges.

    Audio format: PCM int16 mono 16kHz
    """
    await websocket.accept()

    r = await redis.from_url(REDIS_URL)
    pubsub = r.pubsub()

    # Subscribe to nudge stream for this call
    await pubsub.subscribe(f"supervisor:{call_id}:nudges")

    # Initialize variables for cleanup
    audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
    result_queue: asyncio.Queue = None
    transcription_task = None
    processor_task = None
    nudge_task = None

    try:
        # Lazy import Google Chirp-3 Speech
        from .chirp_speech import ChirpSpeechDiarizer, TranscriptSegment

        diarizer = ChirpSpeechDiarizer()
        result_queue: asyncio.Queue = asyncio.Queue()

        async def process_segments():
            """Process transcribed segments from queue."""
            while True:
                segment = await result_queue.get()
                if segment is None:
                    break

                # Publish transcript to UI
                transcript_msg = {
                    "type": "transcript",
                    "speaker": segment.speaker,
                    "text": segment.text,
                    "timestamp": segment.end_time,
                }
                await websocket.send_text(json.dumps(transcript_msg))

                # Publish to Redis for nudge processing
                chunk = {
                    "call_id": call_id,
                    "speaker": segment.speaker,
                    "text": segment.text,
                    "timestamp": segment.end_time,
                }

                await r.publish(
                    f"supervisor:{call_id}:transcript",
                    json.dumps(chunk),
                )

                # Add to nudge processing queue
                await r.xadd(
                    f"supervisor:{call_id}:chunks",
                    {"data": json.dumps(chunk)},
                )

        # Start transcription task
        transcription_task = asyncio.create_task(
            diarizer.transcribe_stream(audio_queue, result_queue)
        )

        # Start segment processor
        processor_task = asyncio.create_task(process_segments())

        # Listen for nudges and forward to client
        async def forward_nudges():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])

        nudge_task = asyncio.create_task(forward_nudges())

        # Receive audio from client
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect()

            if message.get("bytes") is not None:
                # Audio chunk received
                await audio_queue.put(message["bytes"])

    except WebSocketDisconnect:
        pass
    finally:
        # Stop transcription
        if audio_queue:
            await audio_queue.put(None)  # Sentinel
        if result_queue:
            await result_queue.put(None)  # Stop processor

        # Cleanup
        await pubsub.unsubscribe()
        await pubsub.close()
        await r.close()

        # Cancel tasks
        if transcription_task:
            transcription_task.cancel()
        if processor_task:
            processor_task.cancel()
        if nudge_task:
            nudge_task.cancel()
