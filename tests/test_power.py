import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from gateway import power


class FakeStore:
    def __init__(self):
        self.kv = {}

    async def get_state(self, key):
        return self.kv.get(key)

    async def set_state(self, key, value):
        self.kv[key] = value


@pytest.fixture
def client(monkeypatch):
    store = FakeStore()

    async def fake_store():
        return store

    monkeypatch.setattr(power, "get_store", fake_store)
    monkeypatch.setattr(power, "_cache", None)
    app = FastAPI(dependencies=[Depends(power.guard)])
    app.dependency_overrides[power.require_account] = lambda: {"id": "owner"}
    app.include_router(power.router)

    @app.post("/chat")
    async def chat():
        return {"ok": True}

    @app.get("/history/x")
    async def history():
        return {"ok": True}

    @app.post("/auth/login")
    async def login():
        return {"ok": True}

    return TestClient(app)


def test_on_by_default(client):
    assert client.get("/power").json() == {"on": True, "locked": False}
    assert client.post("/chat").status_code == 200


def test_off_blocks_posts_but_not_reads_login_or_switch(client):
    assert client.put("/power", json={"on": False}).json() == {"on": False, "locked": False}
    r = client.post("/chat")
    assert r.status_code == 503 and "switched off" in r.json()["detail"]
    assert client.get("/history/x").status_code == 200
    assert client.post("/auth/login").status_code == 200
    assert client.put("/power", json={"on": True}).json() == {"on": True, "locked": False}
    assert client.post("/chat").status_code == 200


def test_rejects_non_boolean(client):
    assert client.put("/power", json={"on": "no"}).status_code == 400


def test_deploy_switch_is_a_hard_off(client, monkeypatch):
    monkeypatch.setattr(power.settings, "SNOWY_ENABLED", False)
    assert client.get("/power").json() == {"on": False, "locked": True}
    r = client.post("/chat")
    assert r.status_code == 503 and "SNOWY_ENABLED" in r.json()["detail"]
    assert client.put("/power", json={"on": True}).status_code == 409
    assert client.get("/history/x").status_code == 200
    assert client.post("/auth/login").status_code == 200
