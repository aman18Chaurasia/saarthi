"""Nudge emission policy and rate limiting."""
from __future__ import annotations

import hashlib
import os
import time

import redis.asyncio as redis

from .generator import NudgeCandidate

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class NudgePolicy:
    """Enforces nudge emission policies."""

    def __init__(
        self,
        min_confidence: float = 0.7,
        cooldown_sec: int = 30,
        dedupe_window_sec: int = 300,
    ):
        """Initialize policy gate.

        Args:
            min_confidence: Minimum confidence to emit (default 0.7)
            cooldown_sec: Min seconds between nudges (default 30)
            dedupe_window_sec: Dedupe window in seconds (default 300 = 5min)
        """
        self.min_confidence = min_confidence
        self.cooldown_sec = cooldown_sec
        self.dedupe_window_sec = dedupe_window_sec
        self.redis: redis.Redis | None = None

    async def _ensure_redis(self):
        if self.redis is None:
            self.redis = await redis.from_url(REDIS_URL)

    async def check(
        self,
        call_id: str,
        candidate: NudgeCandidate,
        confidence: float,
    ) -> tuple[bool, str]:
        """Check if nudge should be emitted.

        Args:
            call_id: Call identifier
            candidate: Generated nudge
            confidence: Route confidence score

        Returns:
            (should_emit, reason) tuple
        """
        await self._ensure_redis()

        # 1. Confidence check
        if confidence < self.min_confidence:
            return False, f"low_confidence_{confidence:.2f}"

        # 2. Rate limit check
        rate_ok, rate_reason = await self._check_rate_limit(call_id)
        if not rate_ok:
            return False, rate_reason

        # 3. Deduplication check
        dedupe_ok, dedupe_reason = await self._check_dedupe(call_id, candidate)
        if not dedupe_ok:
            return False, dedupe_reason

        # All checks passed - set markers and emit
        await self._set_emit_markers(call_id, candidate)

        return True, "emitted"

    async def _check_rate_limit(self, call_id: str) -> tuple[bool, str]:
        """Check rate limit - max 1 nudge per cooldown period."""
        key = f"supervisor:{call_id}:nudge_last"
        last_ts = await self.redis.get(key)

        if last_ts:
            elapsed = time.time() - float(last_ts)
            if elapsed < self.cooldown_sec:
                remaining = int(self.cooldown_sec - elapsed)
                return False, f"rate_limit_{remaining}s"

        return True, "rate_ok"

    async def _check_dedupe(
        self,
        call_id: str,
        candidate: NudgeCandidate,
    ) -> tuple[bool, str]:
        """Check deduplication - same suggestion hash not sent recently."""
        # Hash suggestion text
        suggestion_hash = hashlib.md5(
            candidate.suggestion.encode("utf-8")
        ).hexdigest()[:8]

        key = f"supervisor:{call_id}:nudge:{suggestion_hash}"
        exists = await self.redis.exists(key)

        if exists:
            return False, "duplicate"

        return True, "dedupe_ok"

    async def _set_emit_markers(self, call_id: str, candidate: NudgeCandidate) -> None:
        """Set Redis markers after successful emit."""
        # Rate limit marker
        rate_key = f"supervisor:{call_id}:nudge_last"
        await self.redis.set(rate_key, time.time())

        # Dedupe marker
        suggestion_hash = hashlib.md5(
            candidate.suggestion.encode("utf-8")
        ).hexdigest()[:8]
        dedupe_key = f"supervisor:{call_id}:nudge:{suggestion_hash}"
        await self.redis.setex(dedupe_key, self.dedupe_window_sec, "1")
