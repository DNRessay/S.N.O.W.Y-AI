import pytest

from agents.orchestrator import OrchestratorAgent


@pytest.mark.asyncio
async def test_run_spawns_one_worker_per_task_and_merges_results():
    agent = OrchestratorAgent(session_id="s1")
    xml = '<task id="t0" type="general"><query>write the report</query></task><task id="t1" type="general"><query>check the numbers</query></task>'
    result = await agent.run({"id": "job1", "xml": xml})

    assert result["task_id"] == "job1"
    assert result["results"]["worker_0"] == {"status": "processed", "query": "write the report", "type": "general"}
    assert result["results"]["worker_1"] == {"status": "processed", "query": "check the numbers", "type": "general"}


@pytest.mark.asyncio
async def test_run_returns_error_for_empty_xml():
    agent = OrchestratorAgent(session_id="s1")
    result = await agent.run({"xml": ""})
    assert result == {"error": "No valid subtasks found in XML payload"}


@pytest.mark.asyncio
async def test_run_rejects_empty_tasks():
    agent = OrchestratorAgent(session_id="s1")
    xml = '<task id="t0" type="general"><query>delegate</query></task>'
    result = await agent.run({"xml": xml})
    assert result["results"]["worker_0"] == {"error": "Task rejected — it must have real content"}


@pytest.mark.asyncio
async def test_fetch_type_task_passes_the_real_url_to_web_fetch(monkeypatch):
    """Regression: this used to call web_fetch with url="" (a literal empty
    string) regardless of the subtask's actual URL, so a fetch-type task
    always failed with "No URL provided" no matter what was asked — the
    query text was silently discarded instead of being used as the URL."""
    captured = {}

    class FakeTools:
        def get(self, name):
            return object()

    async def fake_execute(tool_name, args, session_id=None):
        captured["tool_name"] = tool_name
        captured["args"] = args
        return {"content": "fetched page", "url": args.get("url")}

    monkeypatch.setattr(
        "pipeline.tool_execution.get_tool_execution",
        lambda trust_mode="OPEN": type("E", (), {"execute": staticmethod(fake_execute)})(),
    )

    agent = OrchestratorAgent(tools_registry=FakeTools(), session_id="s1")
    xml = '<task id="t0" type="fetch"><query>https://example.com</query></task>'
    result = await agent.run({"xml": xml})

    assert captured["args"] == {"url": "https://example.com"}
    assert result["results"]["worker_0"] == {"content": "fetched page", "url": "https://example.com"}
