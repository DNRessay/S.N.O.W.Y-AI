import tick_handler


def test_handler_runs_pulse_and_consolidator_and_returns_both_results(monkeypatch):
    calls = []

    class FakePulse:
        async def run_once(self):
            calls.append("pulse")

        def get_audit(self):
            return [{"action": "pulse:tick"}]

    class FakeConsolidator:
        async def run(self, task):
            calls.append("consolidator")
            return {"status": "gates_not_met", "ready": False}

    async def fake_pacific():
        calls.append("pacific")
        return None

    async def fake_automation():
        calls.append("automation")
        return None

    monkeypatch.setattr("tick_handler.PulseDaemon", FakePulse)
    monkeypatch.setattr("tick_handler.ConsolidatorAgent", FakeConsolidator)
    monkeypatch.setattr("tick_handler.refresh_profile", fake_pacific)
    monkeypatch.setattr("tick_handler.run_due_automation", fake_automation)

    result = tick_handler.handler({}, None)

    assert calls == ["pulse", "consolidator", "pacific", "automation"]
    assert result["status"] == "ok"
    assert result["pulse_audit"] == [{"action": "pulse:tick"}]
    assert result["consolidator"] == {"status": "gates_not_met", "ready": False}
