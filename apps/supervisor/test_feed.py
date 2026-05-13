"""Test script to simulate supervisor feed with fake transcript and nudges.

Usage:
    uv run python test_feed.py

Then in browser:
    - Go to Dashboard → Supervisor → Live Monitor
    - Enter call ID: test_call_123
    - Click "Start Monitoring"
    - Watch transcript and nudges appear
"""
import asyncio
import json
import time
from datetime import datetime

import redis.asyncio as redis
from fastapi import WebSocket

# Fake conversation transcript
FAKE_TRANSCRIPT = [
    {"speaker": "agent", "text": "Hello! This is Saarthi calling. Am I speaking with Mr. Sharma?", "delay": 1},
    {"speaker": "customer", "text": "Yes, this is Sharma speaking. Who is this?", "delay": 2},
    {"speaker": "agent", "text": "I'm calling regarding our Personal Loan offer. Do you have a moment?", "delay": 2},
    {"speaker": "customer", "text": "Personal loan? I already have a loan. Not interested.", "delay": 3},
    {"speaker": "agent", "text": "I understand. Could you tell me about your current employment?", "delay": 2},
    {"speaker": "customer", "text": "I work at an IT company. Monthly salary is around 45,000 rupees.", "delay": 3},
    {"speaker": "agent", "text": "That's great! With your income, you qualify for up to 5 lakh loan.", "delay": 2},
    {"speaker": "customer", "text": "What's the interest rate? And I need to check with my wife first.", "delay": 4},
]

# Fake nudges (triggered by customer objections/questions)
FAKE_NUDGES = [
    {
        "turn": 3,  # Trigger after turn 3 (customer says "not interested")
        "route": "OBJECTION",
        "title": "Handle Existing Loan Objection",
        "suggestion": "Acknowledge existing loan. Ask: 'Would debt consolidation at lower rate help?' Emphasize savings potential.",
        "priority": 2,
        "confidence": 0.89,
    },
    {
        "turn": 7,  # Trigger after turn 7 (customer asks about rate + decision maker)
        "route": "PRODUCT_QUESTION",
        "title": "Interest Rate Query",
        "suggestion": "Quote: '10.5% - 14% based on credit score. No prepayment penalty.' Offer to email comparison chart.",
        "priority": 1,
        "confidence": 0.92,
    },
]


async def publish_transcript():
    """Publish fake transcript to Redis for the test call."""
    r = await redis.from_url("redis://localhost:6379/0")
    call_id = "test_call_123"

    print(f"[Test Feed] Publishing transcript for call_id={call_id}")
    print("[Test Feed] Open browser → Supervisor → Live Monitor → enter 'test_call_123' → Start Monitoring\n")

    for idx, turn in enumerate(FAKE_TRANSCRIPT):
        # Publish transcript turn
        await r.publish(
            f"supervisor:{call_id}:transcript",
            json.dumps({
                "type": "transcript",
                "speaker": turn["speaker"],
                "text": turn["text"],
                "timestamp": time.time(),
            })
        )

        print(f"[{turn['speaker'].upper()}] {turn['text']}")

        # Check if nudge should trigger
        for nudge in FAKE_NUDGES:
            if nudge["turn"] == idx:
                await asyncio.sleep(0.5)  # Small delay before nudge
                await r.publish(
                    f"supervisor:{call_id}:nudges",
                    json.dumps({
                        "type": "nudge",
                        "route": nudge["route"],
                        "title": nudge["title"],
                        "suggestion": nudge["suggestion"],
                        "priority": nudge["priority"],
                        "confidence": nudge["confidence"],
                        "transcript": turn["text"],
                        "timestamp": time.time(),
                    })
                )
                print(f"  → [NUDGE: {nudge['route']}] {nudge['title']}")

        await asyncio.sleep(turn["delay"])

    print("\n[Test Feed] Done. Transcript complete.")
    await r.close()


if __name__ == "__main__":
    asyncio.run(publish_transcript())
