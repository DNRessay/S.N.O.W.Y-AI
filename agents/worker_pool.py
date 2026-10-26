import asyncio
from contextvars import ContextVar

from agents.base_agent import BaseAgent

# Isolated context per worker
_agent_context: ContextVar[dict] = ContextVar("agent_context", default={})


class PoolWorker:
    """A single isolated worker_pool worker."""

    def __init__(self, agent_id: str, tools_registry=None):
        self.agent_id = agent_id
        self._tools = tools_registry
        self._log: list[str] = []

    async def execute(self, task: dict) -> dict:
        # Bind isolated context — no bleed between workers
        token = _agent_context.set({"agent_id": self.agent_id, "task": task})
        try:
            query = task.get("query", "")
            self._log.append(f"worker_pool:{self.agent_id}:executing:{query[:60]}")

            # Delegate to GeneralAgent logic within isolated context
            from agents.general_agent import GeneralAgent
            worker = GeneralAgent(tools_registry=self._tools)
            result = await worker.run(task)
            return {"agent_id": self.agent_id, **result}
        finally:
            _agent_context.reset(token)


class WorkerPoolAgent(BaseAgent):
    """
    Spawns parallel workers with contextvars-based context isolation.
    No context bleed between concurrent agents.
    """

    POOL_MEMBERS = ["worker_a", "worker_b", "worker_c"]

    def __init__(self, tools_registry=None, cables_man_ref=None, **kwargs):
        super().__init__(tools_registry, cables_man_ref, **kwargs)
        self._workers: dict[str, PoolWorker] = {
            name: PoolWorker(name, tools_registry)
            for name in self.POOL_MEMBERS
        }

    async def run(self, task: dict) -> dict:
        tasks = task.get("tasks", [task])   # list of subtasks or broadcast single task
        self.log_audit(f"worker_pool:spawn:{len(tasks)}:workers")

        # Assign tasks round-robin across members
        assignments = []
        members = list(self._workers.values())
        for i, t in enumerate(tasks):
            worker = members[i % len(members)]
            assignments.append(worker.execute(t))

        results = await asyncio.gather(*assignments, return_exceptions=True)
        processed = []
        for r in results:
            if isinstance(r, Exception):
                processed.append({"error": str(r)})
            else:
                processed.append(r)

        return {"status": "complete", "worker_count": len(assignments), "results": processed}

    def spawn_parallel(self, tasks: list[dict]) -> list:
        """Synchronous entry: returns a coroutine list for external gather."""
        members = list(self._workers.values())
        return [members[i % len(members)].execute(t) for i, t in enumerate(tasks)]

    def isolate_context(self, agent_id: str, context: dict) -> object:
        """Bind context to this async execution context only."""
        return _agent_context.set({"agent_id": agent_id, **context})
