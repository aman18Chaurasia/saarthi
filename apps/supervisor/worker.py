"""Async worker for processing transcript chunks and generating nudges.

Consumes from Redis streams and runs nudge pipeline.
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
import redis.asyncio as redis

from services.nudge_sidecar import NudgeSidecarPipeline, TranscriptChunk

# Load .env from repo root
repo_root = Path(__file__).parents[2]
env_path = repo_root / ".env"
load_dotenv(env_path)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class SupervisorWorker:
    """Worker that processes transcript chunks."""

    def __init__(self):
        self.pipeline = NudgeSidecarPipeline()
        self.redis: redis.Redis | None = None
        self.running = True

    async def start(self):
        """Start worker main loop."""
        print("[Worker] Starting supervisor nudge worker...")

        self.redis = await redis.from_url(REDIS_URL)

        # Graceful shutdown (Windows-compatible)
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self.stop)

        try:
            await self._consume_loop()
        except KeyboardInterrupt:
            print("[Worker] Keyboard interrupt received")
            self.stop()
        finally:
            await self.redis.close()
            print("[Worker] Shutdown complete")

    def stop(self):
        """Stop worker gracefully."""
        print("[Worker] Shutdown signal received...")
        self.running = False

    async def _consume_loop(self):
        """Main consumption loop - reads from all supervisor streams."""
        # Track last IDs for each stream
        stream_ids: dict[str, str] = {}

        while self.running:
            try:
                # Get all supervisor chunk streams
                keys = await self.redis.keys("supervisor:*:chunks")

                if not keys:
                    # No active streams, wait and retry
                    await asyncio.sleep(1)
                    continue

                # Build streams dict with last IDs
                streams = {}
                for key in keys:
                    key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                    last_id = stream_ids.get(key_str, "$")
                    streams[key_str] = last_id

                # Read from all streams (block 1s)
                messages = await self.redis.xread(streams, block=1000, count=10)

                if not messages:
                    continue

                # Process messages
                for stream_key, msgs in messages:
                    stream_str = (
                        stream_key.decode("utf-8")
                        if isinstance(stream_key, bytes)
                        else stream_key
                    )

                    for msg_id, data in msgs:
                        # Update last ID
                        msg_id_str = (
                            msg_id.decode("utf-8") if isinstance(msg_id, bytes) else msg_id
                        )
                        stream_ids[stream_str] = msg_id_str

                        # Process chunk
                        await self._process_message(data)

            except Exception as exc:
                print(f"[Worker] Error in consume loop: {exc}")
                await asyncio.sleep(1)

    async def _process_message(self, data: dict):
        """Process single transcript chunk message.

        Args:
            data: Redis stream message data
        """
        try:
            # Extract JSON data
            chunk_json = data.get(b"data") or data.get("data")
            if isinstance(chunk_json, bytes):
                chunk_json = chunk_json.decode("utf-8")

            chunk_data = json.loads(chunk_json)

            # Create TranscriptChunk
            chunk = TranscriptChunk(
                call_id=chunk_data["call_id"],
                speaker=chunk_data["speaker"],
                text=chunk_data["text"],
                timestamp=chunk_data.get("timestamp", chunk_data.get("end_time", 0)),
            )

            print(f"[Worker] Processing: {chunk.speaker}: {chunk.text[:50]}...")

            # Process through pipeline
            await self.pipeline.process(chunk)

        except Exception as exc:
            print(f"[Worker] Error processing message: {exc}")
            import traceback
            traceback.print_exc()


async def main():
    """Worker entry point."""
    worker = SupervisorWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
