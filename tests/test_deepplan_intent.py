import pytest

from pipeline.deepplan_intent import (
    detect_deepplan_intent,
    format_deepplan_result,
    run_deepplan_intent,
    deepplan_status_label,
)


def test_detect_deepplan_intent_finds_deep_planning_phrasings():
    assert detect_deepplan_intent("deep plan for the migration") is not None
    assert detect_deepplan_intent("deepplan the launch") is not None
    assert detect_deepplan_intent("think hard about how to scale this") is not None
    assert detect_deepplan_intent("do a deep dive on the architecture") is not None
    assert detect_deepplan_intent("really think through the tradeoffs") is not None


def test_detect_deepplan_intent_returns_the_full_query():
    q = "deep plan for launching the WhatsApp bot"
    assert detect_deepplan_intent(q) == q


def test_detect_deepplan_intent_returns_none_for_ordinary_plan_requests():
    """Must not fire on plain "make a plan for X" — that stays PlanAgent's,
    the quicker/cheaper path."""
    assert detect_deepplan_intent("make a plan for launching the bot") is None
    assert detect_deepplan_intent("help me plan the migration") is None


def test_detect_deepplan_intent_returns_none_for_ordinary_chat():
    assert detect_deepplan_intent("hey, how's it going?") is None


def test_status_label():
    assert "GPT-OSS-120B" in deepplan_status_label()


@pytest.mark.asyncio
async def test_run_deepplan_intent_routes_through_cables_man(monkeypatch):
    calls = []

    class FakeCablesMan:
        async def route(self, task):
            calls.append(task)
            return {"status": "complete", "goal": task["query"], "plan": "the deep plan"}

    monkeypatch.setattr("core.cables_man.CablesMan", FakeCablesMan)
    result = await run_deepplan_intent("deep plan for X", "sess1")

    assert result == {"status": "complete", "goal": "deep plan for X", "plan": "the deep plan"}
    assert calls == [{"query": "deep plan for X", "agent": "deepplan", "session_id": "sess1"}]


@pytest.mark.asyncio
async def test_run_deepplan_intent_returns_empty_dict_on_error(monkeypatch):
    class FakeCablesMan:
        async def route(self, task):
            return {"error": "boom"}

    monkeypatch.setattr("core.cables_man.CablesMan", FakeCablesMan)
    result = await run_deepplan_intent("deep plan for X", "sess1")
    assert result == {}


def test_format_deepplan_result_renders_the_plan():
    out = format_deepplan_result({"plan": "1. Do X\n2. Do Y"})
    assert "Deep Plan" in out
    assert "1. Do X" in out


def test_format_deepplan_result_empty_when_no_plan():
    assert format_deepplan_result({}) == ""
    assert format_deepplan_result({"plan": ""}) == ""
