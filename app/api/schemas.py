# app/api/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ── Requests ───────────────────────────────────────────────────────────────────

class SubjectData(BaseModel):
    firstName:    str
    lastName:     str
    dateOfBirth:  str                        # YYYY-MM-DD
    address:      Optional[str] = None
    city:         Optional[str] = None
    state:        Optional[str] = None
    zip:          Optional[str] = None
    country:      Optional[str] = "US"
    govtIdType:   Optional[str] = None       # Passport / DL / SSN
    govtIdNumber: Optional[str] = None
    middleName:   Optional[str] = None
    nationality:  Optional[str] = None
    ssn:          Optional[str] = None
    county:       Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "firstName":    "Prakash",
                "lastName":     "Kumar",
                "dateOfBirth":  "1990-05-15",
                "address":      "123 Main Street",
                "city":         "Austin",
                "state":        "TX",
                "zip":          "78701",
                "govtIdType":   "Passport",
                "govtIdNumber": "P1234567"
            }
        }
    }


class StartVerificationRequest(BaseModel):
    subjectData: SubjectData


class FeedbackRequest(BaseModel):
    feedback:    str = Field(..., description="Describe what needs re-verification. e.g. 'address info is outdated'")
    subjectData: SubjectData


# ── Responses ──────────────────────────────────────────────────────────────────

class AgentResultOut(BaseModel):
    agentName:         str
    category:          str
    verificationStatus: str
    riskScore:         float
    findings:          str
    flags:             List[str]
    executionMs:       int
    completedAt:       str
    executionType:     str
    cacheIndicator:    str   # FRESH or CACHED


class CategoryReportOut(BaseModel):
    category:    str
    status:      str
    riskScore:   float
    riskLevel:   str
    agentResults: List[AgentResultOut]
    keyFindings: List[str]
    flags:       List[str]


class ExecutiveSummaryOut(BaseModel):
    subjectName:       str
    overallRiskScore:  float
    overallRiskLevel:  str
    recommendation:    str
    totalAgents:       int
    passed:            int
    failed:            int
    warnings:          int
    criticalFlagCount: int
    totalFlagCount:    int
    reportVersion:     int
    isReExecuted:      bool


class SmartReportOut(BaseModel):
    reportId:          str
    verificationId:    str
    subjectId:         str
    reportVersion:     int
    generatedAt:       str
    overallStatus:     str
    overallRiskScore:  float
    overallRiskLevel:  str
    executiveSummary:  ExecutiveSummaryOut
    categoryReports:   Dict[str, CategoryReportOut]
    flagsAndAlerts:    List[Dict[str, Any]]
    auditTrail:        List[Dict[str, Any]]
    executionHistory:  List[Dict[str, Any]]


class VerificationResponse(BaseModel):
    verificationId: str
    subjectId:      str
    message:        str
    report:         SmartReportOut


class FeedbackResponse(BaseModel):
    message:          str
    feedbackText:     str
    reExecutedAgents: List[str]
    cachedAgents:     List[str]
    newVersion:       int
    report:           SmartReportOut
