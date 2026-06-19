# app/agents/criminal_agents.py

import random
from app.agents.base_agent import BaseAgent
from app.utils.helpers import random_delay, maybe_raise


CRIMINAL_SYSTEM_PROMPT = """
You are a criminal background verification agent. Analyze the subject data and return
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
# 1. Federal Criminal Check
# ─────────────────────────────────────────────────────────────
class FederalCriminalCheckAgent(BaseAgent):
    def __init__(self):
        super().__init__("FederalCriminalCheckAgent", "criminal", 2.0)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        if random.random() < 0.04:
            return {
                "status": "FAIL", "risk_score": 95,
                "findings": "Federal criminal record found in PACER. Immediate legal review required.",
                "flags": ["FEDERAL_CRIMINAL_RECORD"],
                "raw_data": {"source": "PACER", "records_found": 1},
            }
        return {
            "status": "PASS", "risk_score": 2,
            "findings": "No federal criminal records found (PACER + FBI databases searched).",
            "flags": [], "raw_data": {"records_found": 0},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run federal criminal background check for:
- Name: {data.get('firstName')} {data.get('lastName')}
- DOB:  {data.get('dateOfBirth')}
- SSN:  {data.get('ssn', 'Not provided')}

Search federal court records (PACER), FBI databases.
Flag any felonies, federal charges, or outstanding warrants.
Return JSON result.
"""
        return await self._ask_ultrasafe(CRIMINAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 2. State Criminal Check
# ─────────────────────────────────────────────────────────────
class StateCriminalCheckAgent(BaseAgent):
    def __init__(self):
        super().__init__("StateCriminalCheckAgent", "criminal", 1.8)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        if random.random() >= 0.06:
            return {
                "status": "PASS", "risk_score": 3,
                "findings": f"No state criminal records found in {data.get('state', 'searched states')}.",
                "flags": [], "raw_data": {"records_found": 0},
            }

        is_felony = random.random() > 0.5
        return {
            "status": "FAIL" if is_felony else "WARNING",
            "risk_score": 85 if is_felony else 45,
            "findings": f"State-level {'felony' if is_felony else 'misdemeanor'} record found in {data.get('state', 'searched states')}.",
            "flags": ["STATE_FELONY" if is_felony else "STATE_MISDEMEANOR"],
            "raw_data": {"type": "felony" if is_felony else "misdemeanor", "records_found": 1},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run state criminal background check for:
- Name:  {data.get('firstName')} {data.get('lastName')}
- DOB:   {data.get('dateOfBirth')}
- State: {data.get('state', 'All states')}

Search state court records for felonies, misdemeanors, and violations.
Return JSON result.
"""
        return await self._ask_ultrasafe(CRIMINAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 3. County Records Check
# ─────────────────────────────────────────────────────────────
class CountyRecordsAgent(BaseAgent):
    def __init__(self):
        super().__init__("CountyRecordsAgent", "criminal", 1.5)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        found = random.random() < 0.05
        return {
            "status": "REVIEW" if found else "PASS",
            "risk_score": 55 if found else 3,
            "findings": "County court record found. Manual review needed." if found else "No county records found. Searched 3 counties.",
            "flags": ["COUNTY_RECORD_REVIEW"] if found else [],
            "raw_data": {"counties_searched": 3, "records_found": 1 if found else 0},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Run county records check for:
- Name:   {data.get('firstName')} {data.get('lastName')}
- DOB:    {data.get('dateOfBirth')}
- County: {data.get('county', 'Not specified')}
- State:  {data.get('state')}

Search county court records, civil records, and local violations.
Return JSON result.
"""
        return await self._ask_ultrasafe(CRIMINAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 4. Sex Offender Registry Agent
# ─────────────────────────────────────────────────────────────
class SexOffenderRegistryAgent(BaseAgent):
    def __init__(self):
        super().__init__("SexOffenderRegistryAgent", "criminal", 2.5)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        found = random.random() < 0.02
        return {
            "status": "FAIL" if found else "PASS",
            "risk_score": 100 if found else 0,
            "findings": "CRITICAL: Subject found on Sex Offender Registry. Do not proceed." if found
                        else "Not listed on National or State sex offender registries.",
            "flags": ["SEX_OFFENDER_REGISTRY_HIT"] if found else [],
            "raw_data": {"registries_checked": ["NSOPW", "State Registry"], "found": found},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Check sex offender registry for:
- Name:  {data.get('firstName')} {data.get('lastName')}
- DOB:   {data.get('dateOfBirth')}
- State: {data.get('state')}

Search National Sex Offender Public Website (NSOPW) and all state registries.
Return JSON result.
"""
        return await self._ask_ultrasafe(CRIMINAL_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 5. Interpol Verification Agent
# ─────────────────────────────────────────────────────────────
class InterpolAgent(BaseAgent):
    def __init__(self):
        super().__init__("InterpolAgent", "criminal", 2.2)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        found = random.random() < 0.01
        return {
            "status": "FAIL" if found else "PASS",
            "risk_score": 100 if found else 0,
            "findings": "CRITICAL: Interpol Red Notice match. Escalate immediately." if found
                        else "No Interpol notices found (Red, Yellow, Blue notices checked).",
            "flags": ["INTERPOL_RED_NOTICE"] if found else [],
            "raw_data": {"notices_checked": ["Red", "Yellow", "Blue", "Black"], "found": found},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Check Interpol database for:
- Name:        {data.get('firstName')} {data.get('lastName')}
- DOB:         {data.get('dateOfBirth')}
- Nationality: {data.get('nationality', 'Not provided')}

Search all Interpol notice types: Red, Yellow, Blue, Black.
Return JSON result.
"""
        return await self._ask_ultrasafe(CRIMINAL_SYSTEM_PROMPT, prompt)
