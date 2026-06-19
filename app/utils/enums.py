# app/utils/enums.py

from enum import Enum


class AgentStatus(str, Enum):
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    CACHED    = "CACHED"
    FRESH     = "FRESH"


class VerificationStatus(str, Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    WARNING = "WARNING"
    REVIEW  = "REVIEW"


class OverallStatus(str, Enum):
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL   = "PARTIAL"
    FAILED    = "FAILED"


class ExecutionType(str, Enum):
    INITIAL     = "INITIAL"
    RE_EXECUTED = "RE_EXECUTED"


class RiskLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


# category risk weights - criminal matters most
RISK_WEIGHTS = {
    "identity":  1.0,
    "criminal":  2.0,
    "financial": 1.5,
}


def get_risk_level(score: float) -> str:
    if score <= 15:  return "LOW"
    if score <= 40:  return "MEDIUM"
    if score <= 70:  return "HIGH"
    return "CRITICAL"


def get_flag_severity(flag: str) -> str:
    critical = ["SANCTIONS_HIT", "SEX_OFFENDER_REGISTRY_HIT", "INTERPOL_RED_NOTICE",
                "FEDERAL_CRIMINAL_RECORD", "FRAUD_INDICATORS"]
    high     = ["STATE_FELONY", "MISSING_GOVT_ID", "PEP_IDENTIFIED", "ADVERSE_MEDIA_HIGH"]
    medium   = ["STATE_MISDEMEANOR", "RECENT_BANKRUPTCY", "COUNTY_RECORD_REVIEW",
                "LOW_CREDIT_SCORE", "ALIAS_DETECTED"]

    if flag in critical: return "CRITICAL"
    if flag in high:     return "HIGH"
    if flag in medium:   return "MEDIUM"
    return "LOW"
