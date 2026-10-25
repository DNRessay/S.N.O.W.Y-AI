import pytest

from agents.companion import Companion, CompanionAgent


class FakeStore:
    def __init__(self):
        self.data: dict[str, dict] = {}

    async def get_companion(self, session_id):
        return self.data.get(session_id)

    async def save_companion(self, session_id, data):
        self.data[session_id] = data


@pytest.mark.asyncio
async def test_status_creates_a_companion_when_none_exists(monkeypatch):
    store = FakeStore()

    async def fake_get_store():
        return store

    monkeypatch.setattr("storage.neon_store.get_store", fake_get_store)
    agent = CompanionAgent(session_id="s1")
    result = await agent.run({"session_id": "s1", "action": "status"})

    assert "name" in result
    assert store.data["s1"]["name"] == result["name"]


@pytest.mark.asyncio
async def test_companion_persists_across_separate_agent_instances(monkeypatch):
    """The whole point of the fix: CablesMan.route() builds a fresh
    CompanionAgent per call, so persistence has to come from the DB, not
    instance state — this proves a second, brand-new CompanionAgent instance
    sees the first instance's changes."""
    store = FakeStore()

    async def fake_get_store():
        return store

    monkeypatch.setattr("storage.neon_store.get_store", fake_get_store)

    agent1 = CompanionAgent(session_id="s1")
    await agent1.run({"session_id": "s1", "action": "new", "name": "Sparky"})

    agent2 = CompanionAgent(session_id="s1")
    fed = await agent2.run({"session_id": "s1", "action": "feed"})

    assert fed["status"]["name"] == "Sparky"
    assert fed["status"]["xp"] == 10


@pytest.mark.asyncio
async def test_different_sessions_get_independent_buddies(monkeypatch):
    store = FakeStore()

    async def fake_get_store():
        return store

    monkeypatch.setattr("storage.neon_store.get_store", fake_get_store)

    agent = CompanionAgent()
    await agent.run({"session_id": "s1", "action": "new", "name": "A"})
    await agent.run({"session_id": "s2", "action": "new", "name": "B"})

    assert store.data["s1"]["name"] == "A"
    assert store.data["s2"]["name"] == "B"


@pytest.mark.asyncio
async def test_rename_persists(monkeypatch):
    store = FakeStore()

    async def fake_get_store():
        return store

    monkeypatch.setattr("storage.neon_store.get_store", fake_get_store)

    agent = CompanionAgent()
    await agent.run({"session_id": "s1", "action": "new"})
    result = await agent.run({"session_id": "s1", "action": "rename", "name": "Newname"})

    assert result["message"] == "Renamed to Newname!"
    assert store.data["s1"]["name"] == "Newname"


@pytest.mark.asyncio
async def test_unknown_action_returns_error_without_writing(monkeypatch):
    store = FakeStore()

    async def fake_get_store():
        return store

    monkeypatch.setattr("storage.neon_store.get_store", fake_get_store)

    agent = CompanionAgent()
    result = await agent.run({"session_id": "s1", "action": "explode"})

    assert "error" in result
    assert "s1" not in store.data


def test_companion_to_dict_from_dict_round_trip_preserves_state():
    companion = Companion(species="Foxbyte", name="Rex")
    companion.gain_xp(150)
    companion.interact("pet")

    restored = Companion.from_dict(companion.to_dict())

    assert restored.name == companion.name
    assert restored.species == companion.species
    assert restored.level == companion.level
    assert restored.xp == companion.xp
    assert restored.xp_next == companion.xp_next
    assert restored.hp == companion.hp
    assert restored.stats == companion.stats
