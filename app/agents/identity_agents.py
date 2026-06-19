# app/agents/identity_agents.py

import random
from datetime import datetime
from app.agents.base_agent import BaseAgent
from app.utils.helpers import random_delay, maybe_raise


IDENTITY_SYSTEM_PROMPT = """
You are a background verification agent. Analyze the subject data provided and return
a JSON verification result. You must return ONLY valid JSON with no extra text.

Required JSON format:
{
    "status": "PASS" | "FAIL" | "WARNING" | "REVIEW",
    "risk_score": <number 0-100>,
    "findings": "<one sentence summary>",
    "flags": ["FLAG_NAME"],
    "raw_data": {}
}
"""


# ─────────────────────────────────────────────────────────────
# 1. Name Validation Agent
# ─────────────────────────────────────────────────────────────
class NameValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__("NameValidationAgent", "identity", 0.8)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        first = data.get("firstName", "").strip()
        last  = data.get("lastName", "").strip()

        if not first or not last or len(first) < 2 or len(last) < 2:
            return {
                "status": "FAIL", "risk_score": 70,
                "findings": "Name could not be verified. First or last name appears incomplete.",
                "flags": ["INVALID_NAME"],
                "raw_data": {"name_valid": False},
            }

        # 10% alias chance
        if random.random() < 0.10:
            return {
                "status": "WARNING", "risk_score": 35,
                "findings": f'Name verified but alias detected: "{first} Jr." — manual review needed.',
                "flags": ["ALIAS_DETECTED"],
                "raw_data": {"name_valid": True, "alias_found": True},
            }

        return {
            "status": "PASS", "risk_score": 5,
            "findings": f'Name "{first} {last}" matched with government records.',
            "flags": [],
            "raw_data": {"name_valid": True},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Perform name validation for the following subject:
- First Name: {data.get('firstName')}
- Last Name: {data.get('lastName')}
- Middle Name: {data.get('middleName', 'N/A')}

Check:
1. Name validity and format
2. Any known aliases or alternate names
3. Name match against public government records

Return JSON result.
"""
        return await self._ask_ultrasafe(IDENTITY_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 2. DOB Verification Agent
# ─────────────────────────────────────────────────────────────
class DOBVerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("DOBVerificationAgent", "identity", 0.9)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        dob_str = data.get("dateOfBirth")
        if not dob_str:
            return {
                "status": "FAIL", "risk_score": 80,
                "findings": "Date of birth not provided.",
                "flags": ["MISSING_DOB"], "raw_data": {},
            }

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            age = (datetime.utcnow() - dob).days / 365.25
        except ValueError:
            return {
                "status": "FAIL", "risk_score": 85,
                "findings": f"Invalid date of birth format: {dob_str}. Use YYYY-MM-DD.",
                "flags": ["INVALID_DOB"], "raw_data": {"provided": dob_str},
            }

        if age < 18:
            return {
                "status": "FAIL", "risk_score": 90,
                "findings": f"Subject is a minor (age: {int(age)}). Cannot proceed.",
                "flags": ["MINOR_DETECTED"], "raw_data": {"age": int(age)},
            }

        return {
            "status": "PASS", "risk_score": 5,
            "findings": f"DOB verified. Subject is {int(age)} years old.",
            "flags": [], "raw_data": {"age": int(age), "dob_valid": True},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Verify date of birth for:
- First Name: {data.get('firstName')}
- Last Name:  {data.get('lastName')}
- DOB:        {data.get('dateOfBirth')}

Check age validity, ensure subject is 18+, and confirm DOB against records.
Return JSON result.
"""
        return await self._ask_ultrasafe(IDENTITY_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 3. Address Verification Agent
# ─────────────────────────────────────────────────────────────
class AddressVerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("AddressVerificationAgent", "identity", 0.7)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        address = data.get("address", "")
        city    = data.get("city", "")
        state   = data.get("state", "")

        if not address or not city or not state:
            return {
                "status": "FAIL", "risk_score": 65,
                "findings": "Address incomplete. Address, city and state are required.",
                "flags": ["INCOMPLETE_ADDRESS"], "raw_data": {"address_provided": False},
            }

        if "PO BOX" in address.upper() or "P.O. BOX" in address.upper():
            return {
                "status": "WARNING", "risk_score": 30,
                "findings": "PO Box detected. Physical street address required for full verification.",
                "flags": ["PO_BOX_ADDRESS"], "raw_data": {"is_po_box": True},
            }

        return {
            "status": "PASS", "risk_score": 8,
            "findings": f"Address verified: {address}, {city}, {state}.",
            "flags": [], "raw_data": {"address_verified": True},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Verify the following address:
- Address: {data.get('address')}
- City:    {data.get('city')}
- State:   {data.get('state')}
- ZIP:     {data.get('zip', 'N/A')}
- Country: {data.get('country', 'US')}

Check address validity, deliverability, and whether it matches subject records.
Return JSON result.
"""
        return await self._ask_ultrasafe(IDENTITY_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 4. Government ID Agent
# ─────────────────────────────────────────────────────────────
class GovernmentIDAgent(BaseAgent):
    def __init__(self):
        super().__init__("GovernmentIDAgent", "identity", 1.2)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        id_number = data.get("govtIdNumber")
        id_type   = data.get("govtIdType")

        if not id_number or not id_type:
            return {
                "status": "FAIL", "risk_score": 85,
                "findings": "No government ID provided. This is a mandatory requirement.",
                "flags": ["MISSING_GOVT_ID"], "raw_data": {"id_provided": False},
            }

        if random.random() < 0.08:
            return {
                "status": "WARNING", "risk_score": 40,
                "findings": f"{id_type} appears expired or near expiry. Submit a renewed document.",
                "flags": ["EXPIRED_ID"], "raw_data": {"id_type": id_type, "expired": True},
            }

        masked = f"****{id_number[-4:]}" if len(id_number) >= 4 else "****"
        return {
            "status": "PASS", "risk_score": 5,
            "findings": f"{id_type} ({masked}) validated successfully.",
            "flags": [], "raw_data": {"id_type": id_type, "verified": True},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Validate government ID:
- ID Type:   {data.get('govtIdType')}
- ID Number: {data.get('govtIdNumber')}
- Name:      {data.get('firstName')} {data.get('lastName')}
- DOB:       {data.get('dateOfBirth')}

Check ID authenticity, expiry status, and name/DOB match.
Return JSON result.
"""
        return await self._ask_ultrasafe(IDENTITY_SYSTEM_PROMPT, prompt)


# ─────────────────────────────────────────────────────────────
# 5. Address History Agent
# ─────────────────────────────────────────────────────────────
class AddressHistoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("AddressHistoryAgent", "identity", 0.6)

    async def _mock_check(self, data: dict) -> dict:
        await random_delay()
        maybe_raise()

        if random.random() < 0.15:
            return {
                "status": "REVIEW", "risk_score": 25,
                "findings": "Address history gap >6 months detected. Manual review recommended.",
                "flags": ["ADDRESS_HISTORY_GAP"],
                "raw_data": {"years_searched": 7, "gap_found": True, "gap_months": 8},
            }

        return {
            "status": "PASS", "risk_score": 8,
            "findings": "Continuous address history verified for the past 7 years.",
            "flags": [], "raw_data": {"years_searched": 7, "gap_found": False},
        }

    async def _real_check(self, data: dict) -> dict:
        prompt = f"""
Verify address history for:
- Name:            {data.get('firstName')} {data.get('lastName')}
- DOB:             {data.get('dateOfBirth')}
- Current Address: {data.get('address')}, {data.get('city')}, {data.get('state')}

Check for address history gaps, inconsistencies, or suspicious patterns over last 7 years.
Return JSON result.
"""
        return await self._ask_ultrasafe(IDENTITY_SYSTEM_PROMPT, prompt)
