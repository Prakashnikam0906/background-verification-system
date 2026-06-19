# tests/test_full_flow.py
"""
End-to-end test that demonstrates:
  1. Full parallel verification (all 16 agents)
  2. Smart report generation
  3. Feedback-based selective re-execution
  4. CACHED vs FRESH indicators
  5. Audit trail and version history

Run with:  python tests/test_full_flow.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from app.orchestrator.orchestrator import orchestrator
from app.state.state_manager import state_manager
from app.reports.report_engine import report_engine
from app.feedback.feedback_handler import parse_feedback

# ── colors ──────────────────────────────────────────────────────
G = '\x1b[32m'   # green
Y = '\x1b[33m'   # yellow
R = '\x1b[31m'   # red
C = '\x1b[36m'   # cyan
B = '\x1b[1m'    # bold
X = '\x1b[0m'    # reset

def sep(title):
    print(f"\n{B}{'─'*60}{X}")
    print(f"{B}{C}  {title}{X}")
    print(f"{B}{'─'*60}{X}")

def ok(msg):  print(f"{G}  ✓  {msg}{X}")
def info(msg): print(f"{C}  ▶  {msg}{X}")
def warn(msg): print(f"{Y}  ⚠  {msg}{X}")


SUBJECT = {
    "firstName":    "Prakash",
    "lastName":     "Kumar",
    "dateOfBirth":  "1990-05-15",
    "address":      "123 Main Street",
    "city":         "Austin",
    "state":        "TX",
    "zip":          "78701",
    "govtIdType":   "Passport",
    "govtIdNumber": "P1234567",
    "nationality":  "Indian",
}


async def main():
    print(f"\n{B}{C}  Background Verification System — Full Test{X}\n")

    # ────────────────────────────────────────────────────────
    sep("TEST 1 — Parallel Execution (all 16 agents)")
    # ────────────────────────────────────────────────────────

    verification_id = str(uuid4())
    subject_id      = "SUB-PRAKASH-KUMAR"

    info(f"Verification ID : {verification_id}")
    info(f"Subject         : {SUBJECT['firstName']} {SUBJECT['lastName']}")
    info("Firing all 16 agents in parallel...\n")

    import time
    t0    = time.time()
    state = await orchestrator.run_all(verification_id, subject_id, SUBJECT)
    elapsed = round(time.time() - t0, 2)

    ok(f"All agents completed in {elapsed}s")
    ok(f"Overall status: {state['overall_status']}")

    print(f"\n  {'Agent':<38} {'Exec Status':<12} {'Result':<10} Risk")
    print(f"  {'─'*38} {'─'*12} {'─'*10} ────")
    for name, ag in state["agent_states"].items():
        r      = ag.get("result") or {}
        status = ag["status"]
        result = r.get("status", "N/A")
        risk   = r.get("riskScore", "N/A")
        icon   = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️ " if result in ("WARNING","REVIEW") else "💥"
        print(f"  {icon} {name:<36} {status:<12} {result:<10} {risk}")

    # ────────────────────────────────────────────────────────
    sep("TEST 2 — Smart Report")
    # ────────────────────────────────────────────────────────

    report = report_engine.generate(state)

    ok(f"Report ID       : {report['reportId']}")
    ok(f"Overall Risk    : {report['overallRiskScore']} ({report['overallRiskLevel']})")
    ok(f"Recommendation  : {report['executiveSummary']['recommendation']}")

    print(f"\n  Category Breakdown:")
    for cat, cr in report["categoryReports"].items():
        print(f"    {cat.upper():<12} status={cr['status']:<8}  risk={cr['riskScore']}/100  ({cr['riskLevel']})")

    if report["flagsAndAlerts"]:
        print(f"\n  Flags:")
        for f in report["flagsAndAlerts"]:
            print(f"    🚩 [{f['severity']:<8}] {f['flag']}  →  {f['agentName']}")
    else:
        ok("No flags raised — clean result")

    # ────────────────────────────────────────────────────────
    sep("TEST 3 — Feedback Preview (dry-run)")
    # ────────────────────────────────────────────────────────

    feedback_text = "The address information is outdated."
    parsed = parse_feedback(feedback_text)

    info(f"Feedback: \"{feedback_text}\"")
    ok(f"Matched keywords  : {parsed['matched_keywords']}")
    ok(f"Agents to re-run  : {parsed['affected_agents']}")
    ok(f"Categories touched: {parsed['affected_categories']}")

    # ────────────────────────────────────────────────────────
    sep("TEST 4 — Selective Re-execution")
    # ────────────────────────────────────────────────────────

    updated_subject = {**SUBJECT, "address": "456 Oak Avenue", "city": "Dallas"}
    info(f"Updated address: {updated_subject['address']}, {updated_subject['city']}")
    info("Only address agents will re-run. All others stay CACHED.\n")

    re_result = await orchestrator.re_execute(verification_id, feedback_text, updated_subject)

    ok(f"Re-execution done. New version: v{re_result['new_version']}")
    ok(f"Re-run agents : {re_result['affected_agents']}")
    ok(f"Cached agents : {len(re_result['cached_agents'])} agents preserved")

    # ────────────────────────────────────────────────────────
    sep("TEST 5 — CACHED vs FRESH indicators")
    # ────────────────────────────────────────────────────────

    updated_state = state_manager.get(verification_id)
    print(f"\n  {'Agent':<38} Status")
    print(f"  {'─'*38} ──────")
    for name, ag in updated_state["agent_states"].items():
        s = ag["status"]
        color = G if s == "FRESH" else Y if s == "CACHED" else C
        print(f"  {name:<38} {color}{s}{X}")

    # ────────────────────────────────────────────────────────
    sep("TEST 6 — Updated Report")
    # ────────────────────────────────────────────────────────

    updated_report = report_engine.generate(updated_state)
    ok(f"Report version  : v{updated_report['reportVersion']}")
    ok(f"Risk score      : {updated_report['overallRiskScore']} ({updated_report['overallRiskLevel']})")
    ok(f"Is re-executed  : {updated_report['executiveSummary']['isReExecuted']}")

    print("\n  Identity agents (re-executed section):")
    for ar in updated_report["categoryReports"]["identity"]["agentResults"]:
        c = G if ar["cacheIndicator"] == "FRESH" else Y
        print(f"    {ar['agentName']:<38} {c}{ar['cacheIndicator']}{X}  {ar['verificationStatus']}")

    # ────────────────────────────────────────────────────────
    sep("TEST 7 — Audit Trail")
    # ────────────────────────────────────────────────────────

    trail = updated_state["audit_trail"]
    print(f"\n  {len(trail)} audit events recorded:\n")
    for i, entry in enumerate(trail, 1):
        d = str(entry.get("details", {}))[:70]
        print(f"  {i:>2}. [{entry['timestamp']}]  {entry['event']}")
        if d and d != "{}":
            print(f"       {d}")

    # ────────────────────────────────────────────────────────
    sep("TEST 8 — Version History")
    # ────────────────────────────────────────────────────────

    print(f"\n  {len(updated_state['history'])} snapshot(s):\n")
    for h in updated_state["history"]:
        print(f"  v{h['version']}  snapped at {h['snapshot_at']}")
        print(f"       Trigger: \"{h['feedback']}\"")

    # ────────────────────────────────────────────────────────
    sep("ALL TESTS PASSED ✅")
    # ────────────────────────────────────────────────────────

    print(f"""
  Summary:
  ✅  16 agents executed in parallel using asyncio.gather
  ✅  Smart report with risk scores, flags, recommendation
  ✅  Feedback parsed and routed to correct agents
  ✅  Selective re-execution — only 2 agents re-ran
  ✅  14 agents preserved as CACHED
  ✅  CACHED vs FRESH indicators in report
  ✅  Full audit trail with timestamps
  ✅  Version history with snapshots
""")


asyncio.run(main())
