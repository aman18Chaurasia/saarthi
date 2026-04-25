"""Nudge event publisher."""
from __future__ import annotations

import json
import os
import time
from typing import Any

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class NudgePublisher:
    """Publishes nudges and decision traces."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client

    async def _ensure_redis(self):
        if self.redis is None:
            self.redis = await redis.from_url(REDIS_URL)

    async def publish_nudge(self, call_id: str, nudge: dict[str, Any]) -> None:
        """Publish approved nudge to UI stream.

        Args:
            call_id: Call identifier
            nudge: Nudge event dict
        """
        await self._ensure_redis()

        # Add metadata
        nudge["type"] = "nudge"
        nudge["call_id"] = call_id
        nudge["timestamp"] = nudge.get("timestamp", time.time())

        # Publish to nudge stream
        await self.redis.publish(
            f"supervisor:{call_id}:nudges",
            json.dumps(nudge),
        )

    async def publish_decision(
        self,
        call_id: str,
        decision: dict[str, Any],
    ) -> None:
        """Publish decision trace (emit or suppress).

        Args:
            call_id: Call identifier
            decision: Decision metadata
        """
        await self._ensure_redis()

        # Add metadata
        decision["call_id"] = call_id
        decision["timestamp"] = time.time()

        # Publish to decision trace stream
        await self.redis.publish(
            f"supervisor:{call_id}:decisions",
            json.dumps(decision),
        )

        # Optional: persist to database for analytics
        # await self._persist_decision(decision)

    async def _persist_decision(self, decision: dict[str, Any]) -> None:
        """Persist decision to MongoDB for analytics.

        TODO: Implement Mongo persistence when needed.
        """
        pass
