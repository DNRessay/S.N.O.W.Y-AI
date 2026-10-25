from agents.base_agent import BaseAgent
from pipeline import llm_providers


class DeepPlanAgent(BaseAgent):
    """
    Deep planning with a big output budget on the free model chain
    — a bigger-budget, slower alternative to PlanAgent's quick pass, for a
    goal that genuinely needs more reasoning. Single bounded call, same
    shape as PlanAgent (agents/plan_agent.py).

    Stateless by design: AgentTool.spawn() (tools/agent_tool.py) builds a
    fresh DeepPlanAgent on every call and Lambda keeps no process between
    invocations, so a multi-request approval flow can't work. The plan is
    returned directly.
    """

    _MAX_TOKENS = 4096

    async def run(self, task: dict) -> dict:
        query = task.get("query", "")
        self.log_audit(f"deepplan:start:{query[:60]}")
        if not query:
            return {"error": "No goal provided to DeepPlanAgent"}

        plan = await self._deep_plan(query)
        return {"status": "complete", "goal": query, "plan": plan}

    async def _deep_plan(self, query: str) -> str:
        """One long, detailed reply on the free chain (Bonsai → Gemini → Groq).
        A failure comes back as a readable message, never an exception."""
        result = await llm_providers.complete("auto", [
            {"role": "system", "content": "You are a deep strategic planner. Think step-by-step, produce a detailed execution plan."},
            {"role": "user", "content": query},
        ], max_tokens=self._MAX_TOKENS)
        if "error" in result:
            return f"Planning failed — {result['error'][:300]}"
        return result.get("content") or "Planning failed — the model returned nothing."
