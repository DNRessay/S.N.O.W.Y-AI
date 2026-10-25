"""Master on/off switch for the whole assistant.

Two layers, either one turns it off:
  1. SNOWY_ENABLED=false (GitHub variable, set on deploy): a hard off. Checked first, never touches the
     database, and the in-app switch cannot override it. The deploy also disables the scheduled tick.
  2. The in-app switch: state in kv_state ("assistant_enabled"), shared by every Lambda.
While off, every POST (chat, tabs, webhooks, MCP, ...) gets a 503 and the tick does nothing. Reading history,
logging in and the switch itself stay available.
"""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from config import settings
from gateway.auth import require_account
from storage.neon_store import get_store

KEY = "assistant_enabled"
CACHE_SECONDS = 5
OFF_MESSAGE = "SNOWY is switched off. Turn it back on from the switch in the header."
LOCKED_MESSAGE = ("SNOWY is switched off by the deploy (SNOWY_ENABLED=false). "
                  "Set the GitHub variable to true and run the deploy again.")
# POSTs that must keep working while off.
EXEMPT_PREFIXES = ("/auth", "/power", "/health", "/runs")

router = APIRouter(prefix="/power")
_cache: tuple[float, bool] | None = None


def locked() -> bool:
    """True when the deploy switched SNOWY off; the in-app switch can't undo that."""
    return not settings.SNOWY_ENABLED


async def is_on() -> bool:
    global _cache
    if locked():
        return False
    now = time.time()
    if _cache and now - _cache[0] < CACHE_SECONDS:
        return _cache[1]
    try:
        value = await (await get_store()).get_state(KEY)
        on = value != "0"
    except Exception as e:  # can't read the switch: stay on rather than lock the owner out
        logging.warning("power switch unreadable, assuming on: %s", e)
        return True
    _cache = (now, on)
    return on


async def set_on(on: bool) -> None:
    global _cache
    await (await get_store()).set_state(KEY, "1" if on else "0")
    _cache = (time.time(), on)


async def guard(request: Request):
    """App-wide dependency: refuse POSTs while the assistant is off."""
    if request.method != "POST" or request.url.path.startswith(EXEMPT_PREFIXES):
        return
    if not await is_on():
        raise HTTPException(503, LOCKED_MESSAGE if locked() else OFF_MESSAGE)


@router.get("")
async def get_power(_account: dict = Depends(require_account)):
    return {"on": await is_on(), "locked": locked()}


@router.put("")
async def put_power(request: Request, _account: dict = Depends(require_account)):
    body = await request.json()
    if not isinstance(body.get("on"), bool):
        raise HTTPException(400, "'on' (true/false) required")
    if locked():
        raise HTTPException(409, LOCKED_MESSAGE)
    await set_on(body["on"])
    return {"on": body["on"], "locked": False}
