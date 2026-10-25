import random
import time

from agents.base_agent import BaseAgent

SPECIES = [
    "Foxbyte",   "Glitchcat", "Neonbat",   "Sparkcub",  "Emberwolf",
    "Frostpup",  "Stormhare", "Voidferret","Lumibear",  "Driftbird",
    "Cipherowl", "Flickrat",  "Phasedeer", "Quartzfox", "Tesselmole",
    "Aurabug",   "Mirrorfish","Echosnake",
]

RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
RARITY_WEIGHTS = [50, 25, 15, 8, 2]

MOODS = ["playful", "curious", "sleepy", "energetic", "focused", "calm"]


class Companion:
    def __init__(self, species: str = None, name: str = None):
        self.species  = species or random.choice(SPECIES)
        self.name     = name or f"{self.species}_{random.randint(100,999)}"
        self.rarity   = random.choices(RARITIES, weights=RARITY_WEIGHTS, k=1)[0]
        self.mood     = random.choice(MOODS)
        self.level    = 1
        self.xp       = 0
        self.xp_next  = 100
        self.hp       = 100
        self.born_at  = time.time()
        self.last_fed = time.time()
        self.stats    = {"energy": 80, "happiness": 90, "focus": 70}

    def interact(self, action: str) -> str:
        if action == "pet":
            self.stats["happiness"] = min(100, self.stats["happiness"] + 5)
            return f"{self.name} purrs happily! 💛"
        elif action == "feed":
            self.stats["energy"] = min(100, self.stats["energy"] + 20)
            self.last_fed = time.time()
            self.gain_xp(10)
            return f"{self.name} munches eagerly! +10 XP 🍖"
        elif action == "train":
            self.stats["focus"] = min(100, self.stats["focus"] + 10)
            self.gain_xp(25)
            return f"{self.name} trains hard! +25 XP 💪"
        elif action == "play":
            self.mood = "playful"
            self.stats["happiness"] = min(100, self.stats["happiness"] + 10)
            self.gain_xp(15)
            return f"{self.name} bounces with joy! +15 XP ✨"
        else:
            return f"{self.name} tilts its head curiously."

    def gain_xp(self, amount: int):
        self.xp += amount
        if self.xp >= self.xp_next:
            self.level += 1
            self.xp -= self.xp_next
            self.xp_next = int(self.xp_next * 1.5)
            self.hp = min(150, self.hp + 10)

    def status(self) -> dict:
        hours_since_fed = (time.time() - self.last_fed) / 3600
        if hours_since_fed > 8:
            self.stats["energy"] = max(0, self.stats["energy"] - 10)

        return {
            "name": self.name,
            "species": self.species,
            "rarity": self.rarity,
            "mood": self.mood,
            "level": self.level,
            "xp": self.xp,
            "xp_next": self.xp_next,
            "hp": self.hp,
            "stats": self.stats,
            "hours_since_fed": round(hours_since_fed, 1),
        }

    def to_dict(self) -> dict:
        return {**self.status(), "born_at": self.born_at, "last_fed": self.last_fed}

    @classmethod
    def from_dict(cls, data: dict) -> "Companion":
        companion = cls(species=data.get("species"), name=data.get("name"))
        companion.rarity  = data.get("rarity", companion.rarity)
        companion.mood    = data.get("mood", companion.mood)
        companion.level   = data.get("level", companion.level)
        companion.xp      = data.get("xp", companion.xp)
        companion.xp_next = data.get("xp_next", companion.xp_next)
        companion.hp      = data.get("hp", companion.hp)
        companion.born_at = data.get("born_at", companion.born_at)
        companion.last_fed = data.get("last_fed", companion.last_fed)
        companion.stats   = data.get("stats", companion.stats)
        return companion


class CompanionAgent(BaseAgent):
    """
    Virtual-pet companion agent: species, rarity tiers, stats, mood.
    One companion per session, persisted in Neon (storage.neon_store.get_companion/
    save_companion) — CablesMan.route() builds a fresh CompanionAgent on every
    call, so keeping the Companion in an in-memory dict (the old approach)
    never actually survived past a single turn; only the DB round-trip
    does.
    """

    async def run(self, task: dict) -> dict:
        session  = task.get("session_id", "default")
        action   = task.get("action", "status")

        from storage.neon_store import get_store
        db = await get_store()
        self.log_audit(f"companion:{session}:{action}")

        if action == "new":
            companion = Companion(species=task.get("species"), name=task.get("name"))
            await db.save_companion(session, companion.to_dict())
            return {"message": f"New companion {companion.name} hatched!", "status": companion.status()}

        companion = await self._load_or_create(db, session)

        if action == "status":
            result = companion.status()
        elif action in ("pet", "feed", "train", "play"):
            message = companion.interact(action)
            result = {"message": message, "status": companion.status()}
        elif action == "rename":
            companion.name = task.get("name", companion.name)
            result = {"message": f"Renamed to {companion.name}!", "status": companion.status()}
        else:
            return {"error": f"Unknown companion action: {action}"}

        await db.save_companion(session, companion.to_dict())
        return result

    async def _load_or_create(self, db, session_id: str) -> Companion:
        data = await db.get_companion(session_id)
        return Companion.from_dict(data) if data else Companion()

    def get_all_species(self) -> list[str]:
        return SPECIES
