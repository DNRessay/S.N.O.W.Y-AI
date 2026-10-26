"""
Medium-tier entrypoint. EventBridge invokes this on a schedule (see template.yaml)
as a stand-in for PULSE's always-on daemon loop, which can't run inside Lambda's
freeze/thaw execution model. Same decision logic, same 15s tick budget — it just
runs once per invocation instead of once per 60s inside an infinite loop.

Also checks CONSOLIDATOR's real (Neon-backed) consolidation gate on the same
schedule — see agents/consolidator_agent.py's docstring for why that gate had to
move out of in-memory instance state. Most ticks are a fast no-op here:
ConsolidatorAgent.run() itself checks the gate first and returns immediately
when it isn't met, same as PulseDaemon.run_once() already does for its
own decision logic.
"""
import asyncio

from agents.consolidator_agent import ConsolidatorAgent
from agents.pulse import PulseDaemon
from pipeline.code_tasks import run_due_automation
from tau.pacific import refresh_profile

# One event loop for the life of the Lambda instance: asyncio.run() made a new loop per invocation and closed
# it, so on a warm instance the database pool and HTTP clients still bound to the old loop failed with
# "Event loop is closed" (the second tick within a few minutes always crashed).
_loop = asyncio.new_event_loop()


def handler(event, context):
    asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(_run())


async def _run():
    from gateway.power import is_on
    if not await is_on():  # the assistant is switched off: no briefs, reminders, CONSOLIDATOR or automations
        return {"status": "off"}
    pulse = PulseDaemon()
    await pulse.run_once()

    consolidator = ConsolidatorAgent()
    consolidator_result = await consolidator.run({})

    # Once a day: re-read the owner's personality/style profile (tau/pacific.py).
    try:
        pacific = await refresh_profile()
    except Exception as e:
        pacific = {"error": str(e)[:300]}

    # One scheduled Code tab automation per tick at most (see pipeline/code_tasks.py).
    try:
        automation = await run_due_automation()
    except Exception as e:  # a broken automation must not take PULSE/CONSOLIDATOR down with it
        automation = {"error": str(e)[:300]}

    # Videos: finish any whose Modal "done" callback was missed (gateway/design_router.advance_all).
    try:
        from gateway.design_router import advance_all
        videos = await advance_all()
    except Exception as e:
        videos = {"error": str(e)[:300]}

    # Facts about the user from the messages since last tick (memory/fact_memory.py).
    try:
        from memory.fact_memory import learn_recent
        facts = await learn_recent()
    except Exception as e:
        facts = {"error": str(e)[:300]}

    return {"status": "ok", "pulse_audit": pulse.get_audit(), "consolidator": consolidator_result, "pacific": pacific,
            "automation": automation, "videos": videos, "facts": facts}
