# app/orchestrator/orchestrator.py

import asyncio
from app.agents.registry import ALL_AGENTS, FEEDBACK_KEYWORDS, CATEGORY_MAP
from app.state.state_manager import state_manager


class Orchestrator:
    """
    Core execution engine.

    run_all()     - fires all 16 agents in parallel (asyncio.gather)
    re_execute()  - re-runs only agents affected by user feedback
    """

    async def run_all(self, verification_id: str, subject_id: str, subject_data: dict) -> dict:
        agent_names = list(ALL_AGENTS.keys())

        print(f"\n[Orchestrator] Starting verification: {verification_id}")
        print(f"[Orchestrator] Launching {len(agent_names)} agents in parallel...\n")

        state_manager.init_verification(verification_id, subject_id, agent_names)

        # fire all agents at the same time
        tasks = [
            self._run_one(verification_id, name, subject_data, "INITIAL")
            for name in agent_names
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        final_state = state_manager.get(verification_id)
        print(f"\n[Orchestrator] All agents done. Overall: {final_state['overall_status']}\n")
        return final_state

    async def re_execute(self, verification_id: str, feedback_text: str, subject_data: dict) -> dict:
        """
        Selective re-execution flow:
        1. Parse feedback → find affected agents
        2. Snapshot current state (version bump)
        3. Mark unaffected agents as CACHED
        4. Re-run only affected agents in parallel
        """
        affected  = self._resolve_agents(feedback_text)
        all_names = list(ALL_AGENTS.keys())

        if not affected:
            return {
                "success": False,
                "message": "No agents matched the feedback keywords. Nothing re-executed.",
                "affected_agents": [],
                "cached_agents": [],
            }

        cached = [n for n in all_names if n not in affected]

        print(f"\n[Orchestrator] Re-executing based on feedback: '{feedback_text}'")
        print(f"[Orchestrator] Re-running {len(affected)} agents: {affected}")
        print(f"[Orchestrator] Caching {len(cached)} agents\n")

        # snapshot + version bump before making any changes
        state_manager.snapshot_and_bump(verification_id, feedback_text)
        state_manager.mark_cached(verification_id, cached)
        state_manager.mark_running(verification_id, affected)

        # re-run only affected agents
        tasks = [
            self._run_one(verification_id, name, subject_data, "RE_EXECUTED")
            for name in affected
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        final_state = state_manager.get(verification_id)
        return {
            "success":         True,
            "message":         f"Re-execution done. {len(affected)} re-run, {len(cached)} cached.",
            "affected_agents": affected,
            "cached_agents":   cached,
            "new_version":     final_state["version"],
        }

    # ── Internal ───────────────────────────────────────────────

    async def _run_one(self, verification_id: str, agent_name: str, subject_data: dict, execution_type: str):
        agent = ALL_AGENTS[agent_name]
        try:
            result = await agent.execute(subject_data)
            state_manager.mark_completed(verification_id, agent_name, result, execution_type)
        except Exception as err:
            print(f"  ✗  [{agent_name}] FAILED: {err}")
            state_manager.mark_failed(verification_id, agent_name, err)

    def _resolve_agents(self, feedback_text: str) -> list:
        lower = feedback_text.lower()
        found = set()
        for keyword, agents in FEEDBACK_KEYWORDS.items():
            if keyword in lower:
                for a in agents:
                    found.add(a)
        return list(found)


# singleton
orchestrator = Orchestrator()
