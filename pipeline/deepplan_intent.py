import re

# "deep plan for X" / "deepplan X" / "think hard about X" — a heavier,
# slower alternative to agent_intent.py's plan_intent: routes to
# DeepPlanAgent (agents/deepplan.py), which uses Groq's larger
# GPT-OSS-120B model instead of the default conversational model, for a
# goal that genuinely needs more reasoning budget than PlanAgent's quick
# pass. Checked before plan_intent in gateway/router.py — "deep plan for
# X" would otherwise also match plan_intent's looser "plan (?:for|to)"
# pattern, and the more specific trigger should win.
_DEEPPLAN_RE = re.compile(
    r"\b(deep plan (?:for|to)|deepplan|think hard about|do a deep dive on|really think through)\b",
    re.I,
)


def detect_deepplan_intent(query: str) -> str | None:
    """Returns the goal (the full query, same "pass it through as-is"
    reasoning as detect_plan_intent) if this looks like a deep-planning
    request, else None."""
    if _DEEPPLAN_RE.search(query):
        return query
    return None


def deepplan_status_label() -> str:
    return "Deep planning (GPT-OSS-120B)…"


async def run_deepplan_intent(goal: str, session_id: str) -> dict:
    """Routes through CablesMan (Step 7) to DeepPlanAgent — a single
    bounded Groq call to the larger planning model. Returns the raw result
    dict, or {} on any failure so a caller can fall back cleanly rather
    than crashing the turn."""
    from core.cables_man import CablesMan
    cables = CablesMan()
    result = await cables.route({
        "query": goal, "agent": "deepplan", "session_id": session_id,
    })
    if not isinstance(result, dict) or result.get("error"):
        return {}
    return result


def format_deepplan_result(result: dict) -> str:
    if not result or not result.get("plan"):
        return ""
    return f"**Deep Plan** _(GPT-OSS-120B)_\n\n{result['plan']}"
