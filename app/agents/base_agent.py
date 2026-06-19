# app/agents/base_agent.py

import time
import json
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from app.utils.helpers import hash_subject_data, now_utc
from app.config.settings import settings


class BaseAgent(ABC):
    """
    Abstract base for all 16 verification agents.

    Two modes:
      - Mock mode  (USE_REAL_API=false): runs simulated checks, no API calls
      - Real mode  (USE_REAL_API=true):  calls UltraSafe via openai-compatible client

    Subclasses implement:
        _mock_check(subject_data) -> dict
        _real_check(subject_data) -> dict

    Both return:
        {
            status:     str,   # PASS | FAIL | WARNING | REVIEW
            risk_score: float, # 0-100
            findings:   str,
            flags:      list,
            raw_data:   dict
        }
    """

    def __init__(self, agent_name: str, category: str, risk_weight: float = 1.0):
        self.agent_name  = agent_name
        self.category    = category
        self.risk_weight = risk_weight

        # shared openai-compatible client for real api calls
        self._client = AsyncOpenAI(
            api_key=settings.ULTRASAFE_API_KEY,
            base_url=settings.ULTRASAFE_BASE_URL,
        )

    async def execute(self, subject_data: dict) -> dict:
        started_ms = int(time.time() * 1000)

        print(f"  ▶  [{self.agent_name}] starting...")

        if settings.USE_REAL_API:
            result = await self._real_check(subject_data)
        else:
            result = await self._mock_check(subject_data)

        elapsed_ms = int(time.time() * 1000) - started_ms

        print(f"  ✓  [{self.agent_name}] {elapsed_ms}ms | {result['status']} | risk={result['risk_score']}")

        return {
            "agentName":   self.agent_name,
            "category":    self.category,
            "status":      result["status"],
            "riskScore":   result["risk_score"],
            "findings":    result["findings"],
            "flags":       result.get("flags", []),
            "rawData":     result.get("raw_data", {}),
            "executionMs": elapsed_ms,
            "completedAt": now_utc(),
            "dataHash":    hash_subject_data(subject_data),
            "mode":        "REAL_API" if settings.USE_REAL_API else "MOCK",
        }

    @abstractmethod
    async def _mock_check(self, subject_data: dict) -> dict:
        pass

    @abstractmethod
    async def _real_check(self, subject_data: dict) -> dict:
        pass

    async def _ask_ultrasafe(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Call UltraSafe API using openai-compatible interface.
        Returns parsed JSON from the model response.
        """
        response = await self._client.chat.completions.create(
            model=settings.ULTRASAFE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0,
            timeout=settings.AGENT_TIMEOUT,
        )

        raw_text = response.choices[0].message.content.strip()

        # strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        return json.loads(raw_text)
