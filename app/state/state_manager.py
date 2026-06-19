# app/state/state_manager.py

import copy
from typing import Dict, Any
from app.utils.helpers import now_utc


class StateManager:
    """
    Tracks execution state for all verifications.

    State structure per verification:
    {
        verification_id,
        subject_id,
        version,           # increments on each re-execution
        created_at,
        updated_at,
        overall_status,    # RUNNING | COMPLETED | PARTIAL | FAILED
        agent_states: {
            agent_name: {
                status,        # RUNNING | COMPLETED | FAILED | CACHED | FRESH
                result,        # full agent output
                started_at,
                completed_at,
                execution_type, # INITIAL | RE_EXECUTED
                data_hash,
                error,
            }
        },
        audit_trail: [ {event, timestamp, details} ],
        history: [ snapshot before each re-execution ],
    }
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}

    # ── Initialize ─────────────────────────────────────────────

    def init_verification(self, verification_id: str, subject_id: str, agent_names: list) -> dict:
        ts = now_utc()

        agent_states = {
            name: {
                "status":         "RUNNING",
                "result":         None,
                "started_at":     ts,
                "completed_at":   None,
                "execution_type": "INITIAL",
                "data_hash":      None,
                "error":          None,
            }
            for name in agent_names
        }

        state = {
            "verification_id": verification_id,
            "subject_id":      subject_id,
            "version":         1,
            "created_at":      ts,
            "updated_at":      ts,
            "overall_status":  "RUNNING",
            "agent_states":    agent_states,
            "audit_trail":     [],
            "history":         [],
        }

        self._add_audit(state, "VERIFICATION_STARTED", {
            "agent_count": len(agent_names),
            "agents": agent_names,
        })

        self._store[verification_id] = state
        return state

    # ── Agent updates ──────────────────────────────────────────

    def mark_completed(self, verification_id: str, agent_name: str, result: dict, execution_type: str = "INITIAL"):
        state = self._get(verification_id)
        ts    = now_utc()
        is_re = execution_type == "RE_EXECUTED"

        state["agent_states"][agent_name].update({
            "status":         "FRESH" if is_re else "COMPLETED",
            "result":         result,
            "completed_at":   ts,
            "execution_type": execution_type,
            "data_hash":      result.get("dataHash"),
            "error":          None,
        })

        state["updated_at"] = ts
        self._add_audit(state, "AGENT_COMPLETED", {
            "agent_name":    agent_name,
            "status":        result.get("status"),
            "risk_score":    result.get("riskScore"),
            "execution_type": execution_type,
            "execution_ms":  result.get("executionMs"),
        })

        self._recalc_status(state)

    def mark_failed(self, verification_id: str, agent_name: str, error: Exception):
        state = self._get(verification_id)
        ts    = now_utc()

        state["agent_states"][agent_name].update({
            "status":       "FAILED",
            "completed_at": ts,
            "error":        str(error),
        })

        state["updated_at"] = ts
        self._add_audit(state, "AGENT_FAILED", {
            "agent_name": agent_name,
            "error":      str(error),
        })
        self._recalc_status(state)

    def mark_cached(self, verification_id: str, agent_names: list):
        state = self._get(verification_id)
        ts    = now_utc()

        for name in agent_names:
            if state["agent_states"][name].get("result"):
                state["agent_states"][name]["status"] = "CACHED"

        state["updated_at"] = ts
        self._add_audit(state, "AGENTS_CACHED", {
            "cached_agents": agent_names,
            "count": len(agent_names),
        })

    def mark_running(self, verification_id: str, agent_names: list):
        state = self._get(verification_id)
        ts    = now_utc()

        for name in agent_names:
            state["agent_states"][name].update({
                "status":         "RUNNING",
                "started_at":     ts,
                "completed_at":   None,
                "execution_type": "RE_EXECUTED",
                "error":          None,
            })

        state["overall_status"] = "RUNNING"
        state["updated_at"]     = ts

    # ── Versioning ─────────────────────────────────────────────

    def snapshot_and_bump(self, verification_id: str, feedback: str):
        state = self._get(verification_id)
        ts    = now_utc()

        # deep copy current state into history before changing anything
        state["history"].append({
            "version":     state["version"],
            "snapshot_at": ts,
            "feedback":    feedback,
            "agent_states": copy.deepcopy(state["agent_states"]),
        })

        state["version"]    += 1
        state["updated_at"]  = ts

        self._add_audit(state, "RE_EXECUTION_STARTED", {
            "feedback":    feedback,
            "new_version": state["version"],
        })

    # ── Read ───────────────────────────────────────────────────

    def get(self, verification_id: str) -> dict:
        return self._get(verification_id)

    def exists(self, verification_id: str) -> bool:
        return verification_id in self._store

    def list_all(self) -> list:
        return [
            {
                "verification_id": s["verification_id"],
                "subject_id":      s["subject_id"],
                "overall_status":  s["overall_status"],
                "version":         s["version"],
                "created_at":      s["created_at"],
                "updated_at":      s["updated_at"],
            }
            for s in self._store.values()
        ]

    # ── Internal ───────────────────────────────────────────────

    def _get(self, verification_id: str) -> dict:
        state = self._store.get(verification_id)
        if not state:
            raise KeyError(f"Verification not found: {verification_id}")
        return state

    def _add_audit(self, state: dict, event: str, details: dict):
        state["audit_trail"].append({
            "event":     event,
            "timestamp": now_utc(),
            "details":   details,
        })

    def _recalc_status(self, state: dict):
        statuses = [a["status"] for a in state["agent_states"].values()]

        if "RUNNING" in statuses:
            state["overall_status"] = "RUNNING"
        elif all(s == "FAILED" for s in statuses):
            state["overall_status"] = "FAILED"
        elif "FAILED" in statuses:
            state["overall_status"] = "PARTIAL"
        else:
            state["overall_status"] = "COMPLETED"
            self._add_audit(state, "VERIFICATION_COMPLETED", {"version": state["version"]})


# singleton
state_manager = StateManager()
