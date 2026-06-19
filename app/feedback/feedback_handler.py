# app/feedback/feedback_handler.py

from app.agents.registry import FEEDBACK_KEYWORDS, CATEGORY_MAP, ALL_AGENTS


def parse_feedback(feedback_text: str) -> dict:
    """
    Parse free-text feedback to determine which agents need re-execution.

    Example:
        "The address information is outdated"
        → matches keyword "address"
        → returns AddressVerificationAgent, AddressHistoryAgent
    """
    lower         = feedback_text.lower()
    matched       = set()
    matched_words = []

    for keyword, agents in FEEDBACK_KEYWORDS.items():
        if keyword in lower:
            matched_words.append(keyword)
            for a in agents:
                matched.add(a)

    affected_agents = list(matched)

    # figure out which categories are touched
    affected_categories = set()
    for cat, agents in CATEGORY_MAP.items():
        if any(a in affected_agents for a in agents):
            affected_categories.add(cat)

    if affected_agents:
        reason = f"Matched keywords: [{', '.join(matched_words)}]. Will re-run {len(affected_agents)} agent(s)."
    else:
        reason = "No matching keywords found. Nothing will be re-executed."

    return {
        "original_feedback":   feedback_text,
        "matched_keywords":    matched_words,
        "affected_agents":     affected_agents,
        "affected_categories": list(affected_categories),
        "reason":              reason,
    }
