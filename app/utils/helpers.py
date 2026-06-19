# app/utils/helpers.py

import hashlib
import json
import asyncio
import random
from datetime import datetime, timezone


def hash_subject_data(data: dict) -> str:
    """hash input data - used for integrity checking and cache invalidation"""
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


async def random_delay(min_ms: int = 300, max_ms: int = 1200):
    """mock network latency"""
    ms = random.randint(min_ms, max_ms)
    await asyncio.sleep(ms / 1000)


def maybe_raise(rate: float = 0.05):
    """simulate 5% agent failure rate - real world scenario"""
    if random.random() < rate:
        raise Exception("External verification service temporarily unavailable")
