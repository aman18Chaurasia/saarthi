"""Seed the database with test call data for all products."""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv(Path(__file__).parents[2] / ".env")

try:
    from .db import engine
    from .models.call import Call
except ImportError:
    from db import engine
    from models.call import Call

PRODUCTS = [
    "personal_loan",
    "home_loan",
    "education_loan",
    "gold_loan",
    "credit_card",
    "unsecured_loan",
    "loan_against_property",
    "commercial_vehicle_loan",
    "four_wheeler_loan",
    "msme_business_loan",
]

OUTCOMES = ["qualified", "not_qualified", "dropped", "no_consent", "callback_requested"]
STATUSES = ["completed", "dropped"]

AGENT_NAMES = ["Priya Sharma", "Rahul Verma", "Sneha Patel", "Amit Kumar"]
LENDER_NAMES = ["HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak Mahindra"]
CUSTOMER_NAMES = ["<NAME_REDACTED>", "<CUSTOMER_NAME_REDACTED>"]


def generate_call_data(product: str, days_ago: int = 0) -> dict:
    """Generate realistic test call data."""
    outcome = random.choice(OUTCOMES)
    status = "completed" if outcome != "dropped" else "dropped"

    duration_s = random.uniform(30, 300) if status == "completed" else random.uniform(5, 30)
    turn_count = random.randint(3, 25) if status == "completed" else random.randint(1, 5)

    started_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    ended_at = started_at + timedelta(seconds=duration_s)

    # Generate realistic latency stats
    asr_latency = random.uniform(50, 150)
    llm_latency = random.uniform(100, 300)
    tts_latency = random.uniform(80, 200)
    e2e_latency = asr_latency + llm_latency + tts_latency

    return {
        "call_id": f"call_{uuid.uuid4().hex[:12]}",
        "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
        "product": product,
        "agent_name": random.choice(AGENT_NAMES),
        "lender_name": random.choice(LENDER_NAMES),
        "customer_name_redacted": random.choice(CUSTOMER_NAMES),
        "status": status,
        "outcome": outcome,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_s": round(duration_s, 2),
        "turn_count": turn_count,
        "error_count": random.randint(0, 2),
        "audio_failed": False,
        "transcript_redacted": [
            {"speaker": "agent", "text": "Hello, this is a test call.", "node": "opener", "turn_index": 0},
            {"speaker": "customer", "text": "Hi, I'm interested.", "node": "qualifier", "turn_index": 1},
        ],
        "latency_stats": {
            "asr_p50": round(asr_latency * 0.9, 2),
            "asr_p95": round(asr_latency * 1.2, 2),
            "llm_p50": round(llm_latency * 0.9, 2),
            "llm_p95": round(llm_latency * 1.2, 2),
            "tts_p50": round(tts_latency * 0.9, 2),
            "tts_p95": round(tts_latency * 1.2, 2),
            "e2e_p50": round(e2e_latency * 0.9, 2),
            "e2e_p95": round(e2e_latency * 1.2, 2),
        },
        "slots_redacted": {},
    }


async def seed_database():
    """Seed the database with test calls."""
    async with AsyncSession(engine) as session:
        # Check if we already have data
        result = await session.exec(select(Call))
        existing_calls = list(result.all())

        if existing_calls:
            print(f"Database already has {len(existing_calls)} calls. Skipping seed.")
            return

        print("Seeding database with test data...")

        calls_created = 0

        # Create 5-15 calls per product over the last 7 days
        for product in PRODUCTS:
            num_calls = random.randint(5, 15)
            print(f"  Creating {num_calls} calls for {product}...")

            for i in range(num_calls):
                days_ago = random.randint(0, 7)
                call_data = generate_call_data(product, days_ago)
                call = Call(**call_data)
                session.add(call)
                calls_created += 1

        await session.commit()
        print(f"Successfully created {calls_created} test calls across {len(PRODUCTS)} products!")


async def clear_database():
    """Clear all calls from the database (use with caution!)."""
    async with AsyncSession(engine) as session:
        result = await session.exec(select(Call))
        calls = list(result.all())

        if not calls:
            print("Database is already empty.")
            return

        print(f"Deleting {len(calls)} calls...")
        for call in calls:
            await session.delete(call)

        await session.commit()
        print("Database cleared!")


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await clear_database()
    else:
        await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
