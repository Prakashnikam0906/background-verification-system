# app/api/routes/verification.py

from fastapi import APIRouter, HTTPException
from uuid import uuid4
from app.api.schemas import (
    StartVerificationRequest,
    FeedbackRequest,
    VerificationResponse,
    FeedbackResponse,
)
from app.orchestrator.orchestrator import orchestrator
from app.state.state_manager import state_manager
from app.reports.report_engine import report_engine
from app.feedback.feedback_handler import parse_feedback

router = APIRouter(prefix="/api/v1", tags=["Verification"])


# ── POST /verify ───────────────────────────────────────────────────────────────
@router.post("/verify", response_model=VerificationResponse, status_code=201)
async def start_verification(body: StartVerificationRequest):
    """
    Start a full background verification.
    All 16 agents run in parallel.
    Returns a complete smart report when done.
    """
    verification_id = str(uuid4())
    subject_data    = body.subjectData.model_dump()
    subject_id      = f"SUB-{body.subjectData.firstName.upper()}-{body.subjectData.lastName.upper()}"

    final_state = await orchestrator.run_all(verification_id, subject_id, subject_data)
    report      = report_engine.generate(final_state)

    return {
        "verificationId": verification_id,
        "subjectId":      subject_id,
        "message":        "Verification completed successfully.",
        "report":         report,
    }


# ── GET /verify/{id}/report ────────────────────────────────────────────────────
@router.get("/verify/{verification_id}/report")
async def get_report(verification_id: str):
    """Get the latest smart report for a verification."""
    if not state_manager.exists(verification_id):
        raise HTTPException(status_code=404, detail=f"Verification {verification_id} not found.")
    state  = state_manager.get(verification_id)
    report = report_engine.generate(state)
    return report


# ── GET /verify/{id}/state ─────────────────────────────────────────────────────
@router.get("/verify/{verification_id}/state")
async def get_state(verification_id: str):
    """Get raw execution state including audit trail and history."""
    if not state_manager.exists(verification_id):
        raise HTTPException(status_code=404, detail=f"Verification {verification_id} not found.")
    return state_manager.get(verification_id)


# ── POST /verify/{id}/feedback ─────────────────────────────────────────────────
@router.post("/verify/{verification_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(verification_id: str, body: FeedbackRequest):
    """
    Submit feedback for selective re-execution.

    Example feedback: "The address information is outdated."
    → Only AddressVerificationAgent and AddressHistoryAgent re-run.
    → All other agents stay CACHED.
    → Report updated with FRESH/CACHED indicators.
    """
    if not state_manager.exists(verification_id):
        raise HTTPException(status_code=404, detail=f"Verification {verification_id} not found.")

    subject_data = body.subjectData.model_dump()
    result       = await orchestrator.re_execute(verification_id, body.feedback, subject_data)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    state  = state_manager.get(verification_id)
    report = report_engine.generate(state)

    return {
        "message":          result["message"],
        "feedbackText":     body.feedback,
        "reExecutedAgents": result["affected_agents"],
        "cachedAgents":     result["cached_agents"],
        "newVersion":       result["new_version"],
        "report":           report,
    }


# ── POST /verify/{id}/feedback/preview ─────────────────────────────────────────
@router.post("/verify/{verification_id}/feedback/preview")
async def preview_feedback(verification_id: str, body: dict):
    """
    Dry-run: shows which agents would re-execute for a given feedback string.
    Does not actually re-execute anything.
    """
    feedback = body.get("feedback", "")
    if not feedback:
        raise HTTPException(status_code=400, detail="feedback field is required.")
    return parse_feedback(feedback)


# ── GET /verifications ──────────────────────────────────────────────────────────
@router.get("/verifications")
async def list_verifications():
    """List all verification runs."""
    return state_manager.list_all()
