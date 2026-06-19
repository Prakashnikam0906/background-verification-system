# app/agents/financial_agents.py

import random
from app.agents.base_agent import BaseAgent
from app.utils.helpers import random_delay, maybe_raise


FINANCIAL_SYSTEM_PROMPT = """
You are a financial and fraud verification agent. Analyze the subject data and return
a JSON verification result. Return ONLY valid JSON, no extra text.

Required format:
{
    "status": "PASS" | "FAIL" | "WARNING" | "REVIEW",
    "risk_score": <number 0-100>,
    "findings": "<one sentence summary>",
    "flags": ["FLAG_NAME"],
    "raw_data": {}
}
"""


# ─────────────────────────────────────────────────────────────
# 1. Credit Verification
# ─────────────────────────────────────────────────────────────
class CreditVerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("CreditVerificationAgent", "financial", 1.0)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        score = random.randint(400, 800)

        if score >= 700:
            return {
                "status": "PASS",
                "risk_score": round((800 - score) / 10),
                "findings": f"Credit score {score} — good standing, no concerns.",
                "flags": [], "raw_data": {"credit_score": score, "bureau": "Equifax", "rating": "Good"},
            }
        if score >= 580:
            return {
                "status": "WARNING", "risk_score": 40,
                "findings": f"Credit score {score} — fair credit, some irregularities noted.",
                "flags": [], "raw_data": {"credit_score": score, "bureau": "Equifax", "rating": "Fair"},
            }
        return {
            "status": "FAIL", "risk_score": 65,
            "findings": f"Credit score {score} — poor credit history, multiple delinquencies.",
            "flags": ["LOW_CREDIT_SCORE"],
            "raw_data": {"credit_score": score, "bureau": "Equifax", "rating": "Poor"},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run credit verification for:
- Name:    {data.get('firstName')} {data.get('lastName')}
- DOB:     {data.get('dateOfBirth')}
- Address: {data.get('address')}, {data.get('city')}, {data.get('state')}
- SSN:     {data.get('ssn', 'Not provided')}

Check credit score, payment history, delinquencies, and credit utilization.
Return JSON result.
"""
        return await self._ask_ultrasafe(FINANCIAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 2. Fraud Detection
# ─────────────────────────────────────────────────────────────
class FraudDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("FraudDetectionAgent", "financial", 1.8)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        detected = random.random() < 0.07
        return {
            "status": "FAIL" if detected else "PASS",
            "risk_score": 90 if detected else 5,
            "findings": "Fraud indicators detected — suspicious identity pattern matching." if detected
                        else "No fraud indicators detected. All 24 fraud signals cleared.",
            "flags": ["FRAUD_INDICATORS"] if detected else [],
            "raw_data": {"signals_checked": 24, "signals_flagged": 3 if detected else 0},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run fraud detection analysis for:
- Name:    {data.get('firstName')} {data.get('lastName')}
- DOB:     {data.get('dateOfBirth')}
- Address: {data.get('address')}
- Govt ID: {data.get('govtIdNumber', 'Not provided')}

Analyze for identity fraud, synthetic identity, document fraud, and suspicious patterns.
Return JSON result.
"""
        return await self._ask_ultrasafe(FINANCIAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 3. Sanctions Screening
# ─────────────────────────────────────────────────────────────
class SanctionsScreeningAgent(BaseAgent):
    def __init__(self):
        super().__init__("SanctionsScreeningAgent", "financial", 2.3)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        hit = random.random() < 0.02
        return {
            "status": "FAIL" if hit else "PASS",
            "risk_score": 100 if hit else 0,
            "findings": "CRITICAL: Match found on OFAC SDN list. Transaction legally prohibited." if hit
                        else "No sanctions matches found (OFAC, UN, EU, UK HMT).",
            "flags": ["SANCTIONS_HIT"] if hit else [],
            "raw_data": {"lists_checked": ["OFAC SDN", "UN Security Council", "EU Consolidated", "UK HMT"], "match_found": hit},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run sanctions screening for:
- Name:        {data.get('firstName')} {data.get('lastName')}
- DOB:         {data.get('dateOfBirth')}
- Nationality: {data.get('nationality', 'Not provided')}

Search OFAC SDN, UN Security Council, EU Consolidated List, UK HMT, and other sanctions databases.
Return JSON result.
"""
        return await self._ask_ultrasafe(FINANCIAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 4. Bankruptcy Check
# ─────────────────────────────────────────────────────────────
class BankruptcyCheckAgent(BaseAgent):
    def __init__(self):
        super().__init__("BankruptcyCheckAgent", "financial", 1.2)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        found = random.random() < 0.08
        if not found:
            return {
                "status": "PASS", "risk_score": 5,
                "findings": "No bankruptcy filings found.",
                "flags": [], "raw_data": {"filings_found": 0},
            }

        recent = random.random() < 0.4
        return {
            "status": "FAIL" if recent else "WARNING",
            "risk_score": 70 if recent else 35,
            "findings": f"Bankruptcy filing found ({'within last 5 years — Chapter 7' if recent else '5+ years ago, discharged'}).",
            "flags": ["RECENT_BANKRUPTCY" if recent else "PRIOR_BANKRUPTCY"],
            "raw_data": {"filings_found": 1, "type": "Chapter 7", "years_ago": 2 if recent else 8},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run bankruptcy check for:
- Name: {data.get('firstName')} {data.get('lastName')}
- DOB:  {data.get('dateOfBirth')}
- SSN:  {data.get('ssn', 'Not provided')}

Search PACER bankruptcy courts for Chapter 7, Chapter 11, Chapter 13 filings.
Return JSON result.
"""
        return await self._ask_ultrasafe(FINANCIAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 5. PEP Screening
# ─────────────────────────────────────────────────────────────
class PEPScreeningAgent(BaseAgent):
    def __init__(self):
        super().__init__("PEPScreeningAgent", "financial", 1.9)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        is_pep = random.random() < 0.04
        return {
            "status": "REVIEW" if is_pep else "PASS",
            "risk_score": 65 if is_pep else 2,
            "findings": "Subject identified as PEP (Politically Exposed Person). Enhanced due diligence required." if is_pep
                        else "No PEP designation found (World-Check + Dow Jones searched).",
            "flags": ["PEP_IDENTIFIED"] if is_pep else [],
            "raw_data": {"is_pep": is_pep, "databases": ["World-Check", "Dow Jones Risk & Compliance"]},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run PEP (Politically Exposed Person) screening for:
- Name:        {data.get('firstName')} {data.get('lastName')}
- DOB:         {data.get('dateOfBirth')}
- Nationality: {data.get('nationality', 'Not provided')}

Search World-Check, Dow Jones Risk & Compliance, and government databases.
Return JSON result.
"""
        return await self._ask_ultrasafe(FINANCIAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 6. Adverse Media Agent
# ─────────────────────────────────────────────────────────────
class AdverseMediaAgent(BaseAgent):
    def __init__(self):
        super().__init__("AdverseMediaAgent", "financial", 1.1)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        found = random.random() < 0.10
        if not found:
            return {
                "status": "PASS", "risk_score": 5,
                "findings": "No adverse media coverage found.",
                "flags": [], "raw_data": {"articles_found": 0},
            }

        severity = random.choice(["LOW", "MEDIUM", "HIGH"])
        score_map = {"LOW": 15, "MEDIUM": 40, "HIGH": 75}
        return {
            "status": "FAIL" if severity == "HIGH" else "WARNING",
            "risk_score": score_map[severity],
            "findings": f"Adverse media found ({severity} severity) — financial misconduct allegations in news.",
            "flags": [f"ADVERSE_MEDIA_{severity}"],
            "raw_data": {"articles_found": random.randint(1, 5), "severity": severity},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run adverse media screening for:
- Name: {data.get('firstName')} {data.get('lastName')}
- DOB:  {data.get('dateOfBirth')}

Search news articles, press releases, and online sources for negative coverage involving:
fraud, corruption, money laundering, criminal activity, or regulatory violations.
Return JSON result.
"""
        return await self._ask_ultrasafe(FINANCIAL_SYSTEM_PROMPT, prompt)
