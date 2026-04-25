"""Context manager for supervisor transcription history.

Maintains rolling window of recent transcript turns in Redis.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class NudgeContextManager:
    """Manages conversation context for nudge generation."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client

    async def _ensure_redis(self):
        if self.redis is None:
            self.redis = await redis.from_url(REDIS_URL)

    async def append_turn(
        self,
        call_id: str,
        speaker: str,
        text: str,
        timestamp: float | None = None,
    ) -> None:
        """Add new turn to conversation context.

        Args:
            call_id: Call identifier
            speaker: "agent" or "customer"
            text: Transcript text
            timestamp: Unix timestamp (defaults to now)
        """
        await self._ensure_redis()

        key = f"supervisor:{call_id}:context"

        turn = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp or time.time(),
        }

        # Prepend to list (newest first)
        await self.redis.lpush(key, json.dumps(turn))

        # Keep only last 20 turns
        await self.redis.ltrim(key, 0, 19)

        # Expire after 1 hour
        await self.redis.expire(key, 3600)

    async def get_context(self, call_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent conversation turns.

        Args:
            call_id: Call identifier
            limit: Max turns to retrieve (default 20)

        Returns:
            List of turns (newest first)
        """
        await self._ensure_redis()

        key = f"supervisor:{call_id}:context"
        raw_turns = await self.redis.lrange(key, 0, limit - 1)

        turns = [json.loads(t) for t in raw_turns]

        # Reverse to get chronological order (oldest first)
        return list(reversed(turns))

    async def get_last_customer_turn(self, call_id: str) -> dict[str, Any] | None:
        """Get most recent customer turn.

        Args:
            call_id: Call identifier

        Returns:
            Customer turn dict or None
        """
        context = await self.get_context(call_id, limit=10)

        for turn in reversed(context):  # Search newest first
            if turn["speaker"] == "customer":
                return turn

        return None

    async def clear(self, call_id: str) -> None:
        """Clear context for call.

        Args:
            call_id: Call identifier
        """
        await self._ensure_redis()
        key = f"supervisor:{call_id}:context"
        await self.redis.delete(key)
