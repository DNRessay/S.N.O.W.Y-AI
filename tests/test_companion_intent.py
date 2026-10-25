import pytest

from pipeline.companion_intent import (
    companion_status_label,
    detect_companion_intent,
    format_companion_result,
    run_companion_intent,
)


def test_detect_companion_intent_status_phrasings():
    for msg in ["companion", "Companion", "companion status", "check my companion", "show the companion", "my companion"]:
        assert detect_companion_intent(msg) == {"action": "status"}, msg


def test_detect_companion_intent_action_phrasings():
    assert detect_companion_intent("pet my companion") == {"action": "pet"}
    assert detect_companion_intent("feed the companion") == {"action": "feed"}
    assert detect_companion_intent("train my companion") == {"action": "train"}
    assert detect_companion_intent("play with my companion") == {"action": "play"}


def test_detect_companion_intent_new_phrasings():
    for msg in ["hatch a companion", "get a companion", "hatch me a companion", "create a new companion", "start a companion"]:
        assert detect_companion_intent(msg) == {"action": "new"}, msg


def test_detect_companion_intent_rename():
    assert detect_companion_intent("rename my companion to Spark") == {"action": "rename", "name": "Spark"}
    assert detect_companion_intent("rename companion to Ember") == {"action": "rename", "name": "Ember"}


def test_detect_companion_intent_returns_none_for_unrelated_mentions():
    """"companion" appearing inside an ordinary sentence must not misfire —
    same false-positive shape already fixed for bash_intent/continue_intent
    this session."""
    assert detect_companion_intent("my companion Dave said hi") is None
    assert detect_companion_intent("hey, how's it going?") is None
    assert detect_companion_intent("") is None


def test_companion_status_label():
    assert companion_status_label("pet") == "Petting your companion…"
    assert companion_status_label("unknown") == "Working with your companion…"


def test_format_companion_result_status():
    status = {
        "name": "Sparkcub_123", "species": "Sparkcub", "rarity": "Rare", "mood": "playful",
        "level": 2, "xp": 10, "xp_next": 150, "hp": 110,
        "stats": {"energy": 80, "happiness": 90, "focus": 70},
    }
    out = format_companion_result("status", status)
    assert "Sparkcub_123" in out
    assert "Rare" in out
    assert "Level 2" in out


def test_format_companion_result_status_with_no_companion_yet():
    out = format_companion_result("status", {})
    assert "no companion yet" in out.lower()


def test_format_companion_result_interact():
    result = {"message": "Sparkcub_123 purrs happily! 💛", "status": {"name": "Sparkcub_123", "species": "x",
              "rarity": "y", "mood": "z", "level": 1, "xp": 0, "xp_next": 100, "hp": 100,
              "stats": {"energy": 80, "happiness": 90, "focus": 70}}}
    out = format_companion_result("pet", result)
    assert "purrs happily" in out
    assert "Sparkcub_123" in out


def test_format_companion_result_error():
    out = format_companion_result("pet", {"error": "Unknown companion action: pet"})
    assert "couldn't reach your companion" in out.lower()


@pytest.mark.asyncio
async def test_run_companion_intent_routes_through_cables_man(monkeypatch):
    calls = []

    class FakeCablesMan:
        async def route(self, task):
            calls.append(task)
            return {"name": "x", "status": "ok"}

    monkeypatch.setattr("core.cables_man.CablesMan", FakeCablesMan)
    result = await run_companion_intent({"action": "status"}, "sess1")
    assert result == {"name": "x", "status": "ok"}
    assert calls == [{"agent": "companion", "action": "status", "session_id": "sess1"}]


@pytest.mark.asyncio
async def test_run_companion_intent_passes_name_for_rename(monkeypatch):
    calls = []

    class FakeCablesMan:
        async def route(self, task):
            calls.append(task)
            return {"message": "Renamed to Spark!"}

    monkeypatch.setattr("core.cables_man.CablesMan", FakeCablesMan)
    await run_companion_intent({"action": "rename", "name": "Spark"}, "sess1")
    assert calls == [{"agent": "companion", "action": "rename", "session_id": "sess1", "name": "Spark"}]


@pytest.mark.asyncio
async def test_run_companion_intent_returns_error_dict_on_unexpected_shape(monkeypatch):
    class FakeCablesMan:
        async def route(self, task):
            return "not a dict"

    monkeypatch.setattr("core.cables_man.CablesMan", FakeCablesMan)
    result = await run_companion_intent({"action": "status"}, "sess1")
    assert result == {"error": "companion agent returned an unexpected result"}
