# app/reports/report_engine.py

from app.agents.registry import CATEGORY_MAP
from app.utils.enums import RISK_WEIGHTS, get_risk_level, get_flag_severity
from app.utils.helpers import now_utc


class ReportEngine:

    def generate(self, state: dict) -> dict:
        category_reports = self._build_category_reports(state)
        overall_risk     = self._calc_overall_risk(category_reports)
        all_flags        = self._collect_flags(state)
        exec_summary     = self._build_summary(state, overall_risk, all_flags, category_reports)

        vid = state["verification_id"]
        return {
            "reportId":         f"RPT-{vid[:8].upper()}",
            "verificationId":   vid,
            "subjectId":        state["subject_id"],
            "reportVersion":    state["version"],
            "generatedAt":      now_utc(),
            "overallStatus":    state["overall_status"],
            "overallRiskScore": overall_risk["score"],
            "overallRiskLevel": overall_risk["level"],
            "executiveSummary": exec_summary,
            "categoryReports":  category_reports,
            "flagsAndAlerts":   all_flags,
            "auditTrail":       state["audit_trail"],
            "executionHistory": [
                {
                    "version":     h["version"],
                    "snapshotAt":  h["snapshot_at"],
                    "feedback":    h["feedback"],
                    "agentCount":  len(h["agent_states"]),
                }
                for h in state.get("history", [])
            ],
        }

    # ── Category reports ───────────────────────────────────────

    def _build_category_reports(self, state: dict) -> dict:
        reports = {}

        for category, agent_names in CATEGORY_MAP.items():
            agent_results = []
            total_risk    = 0
            count         = 0
            cat_flags     = []
            key_findings  = []

            for name in agent_names:
                ag = state["agent_states"].get(name)
                if not ag:
                    continue

                result = ag.get("result") or {}
                v_status = result.get("status", "N/A")
                r_score  = result.get("riskScore", 0)
                findings = result.get("findings", ag.get("error", "Pending..."))
                flags    = result.get("flags", [])
                e_type   = ag.get("execution_type", "INITIAL")
                cache_ind = "CACHED" if ag["status"] == "CACHED" else "FRESH"

                agent_results.append({
                    "agentName":          name,
                    "category":           category,
                    "verificationStatus": v_status,
                    "riskScore":          r_score,
                    "findings":           findings,
                    "flags":              flags,
                    "executionMs":        result.get("executionMs", 0),
                    "completedAt":        ag.get("completed_at", ""),
                    "executionType":      e_type,
                    "cacheIndicator":     cache_ind,
                })

                if ag["status"] in ("COMPLETED", "FRESH", "CACHED"):
                    total_risk += r_score
                    count += 1

                cat_flags.extend(flags)
                if v_status in ("FAIL", "WARNING", "REVIEW"):
                    key_findings.append(f"[{v_status}] {name}: {findings}")

            cat_risk   = round(total_risk / count, 1) if count else 0
            cat_status = self._calc_category_status(agent_results)

            reports[category] = {
                "category":    category,
                "status":      cat_status,
                "riskScore":   cat_risk,
                "riskLevel":   get_risk_level(cat_risk),
                "agentResults": agent_results,
                "keyFindings": key_findings,
                "flags":       cat_flags,
            }

        return reports

    def _calc_category_status(self, agent_results: list) -> str:
        statuses = [a["verificationStatus"] for a in agent_results if a["verificationStatus"] != "N/A"]
        if "FAIL"    in statuses: return "FAIL"
        if "REVIEW"  in statuses: return "REVIEW"
        if "WARNING" in statuses: return "WARNING"
        if all(s == "PASS" for s in statuses): return "PASS"
        return "PENDING"

    # ── Overall risk ───────────────────────────────────────────

    def _calc_overall_risk(self, category_reports: dict) -> dict:
        total_weight = 0
        weighted_sum = 0

        for cat, report in category_reports.items():
            w = RISK_WEIGHTS.get(cat, 1.0)
            weighted_sum += report["riskScore"] * w
            total_weight += w

        score = round(weighted_sum / total_weight, 1) if total_weight else 0
        return {"score": score, "level": get_risk_level(score)}

    # ── Flags ──────────────────────────────────────────────────

    def _collect_flags(self, state: dict) -> list:
        flags = []
        for agent_name, ag in state["agent_states"].items():
            for f in (ag.get("result") or {}).get("flags", []):
                flags.append({
                    "flag":      f,
                    "agentName": agent_name,
                    "severity":  get_flag_severity(f),
                    "timestamp": ag.get("completed_at"),
                })

        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return sorted(flags, key=lambda x: order.get(x["severity"], 4))

    # ── Executive summary ──────────────────────────────────────

    def _build_summary(self, state: dict, overall_risk: dict, all_flags: list, category_reports: dict) -> dict:
        agent_states   = state["agent_states"]
        results        = [ag.get("result") or {} for ag in agent_states.values()]
        critical_flags = [f for f in all_flags if f["severity"] == "CRITICAL"]

        passed   = sum(1 for r in results if r.get("status") == "PASS")
        failed   = sum(1 for r in results if r.get("status") == "FAIL")
        warnings = sum(1 for r in results if r.get("status") in ("WARNING", "REVIEW"))

        if critical_flags:
            recommendation = "DO NOT PROCEED — Critical flags require immediate legal review."
        elif overall_risk["level"] == "HIGH":
            recommendation = "PROCEED WITH CAUTION — Elevated risk. Senior review recommended."
        elif overall_risk["level"] == "MEDIUM":
            recommendation = "CONDITIONAL APPROVAL — Some items need clarification."
        else:
            recommendation = "APPROVED — Background verification passed with low risk."

        subject_id = state["subject_id"]
        return {
            "subjectName":       subject_id,
            "overallRiskScore":  overall_risk["score"],
            "overallRiskLevel":  overall_risk["level"],
            "recommendation":    recommendation,
            "totalAgents":       len(agent_states),
            "passed":            passed,
            "failed":            failed,
            "warnings":          warnings,
            "criticalFlagCount": len(critical_flags),
            "totalFlagCount":    len(all_flags),
            "reportVersion":     state["version"],
            "isReExecuted":      state["version"] > 1,
            "categorySummary":   {
                cat: {"status": r["status"], "riskScore": r["riskScore"], "riskLevel": r["riskLevel"]}
                for cat, r in category_reports.items()
            },
        }


# singleton
report_engine = ReportEngine()
