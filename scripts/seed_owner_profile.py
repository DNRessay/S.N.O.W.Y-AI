import asyncio
import json
import os
import sys
import time

import asyncpg


async def main():
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        sys.exit("Error: NEON_DATABASE_URL environment variable is not set.")

    raw_profile = os.environ.get("OWNER_PROFILE_JSON", "").strip()
    if not raw_profile:
        sys.exit(
            "Error: OWNER_PROFILE_JSON environment variable (or repository secret) is empty or not set.\n"
            "Please configure the OWNER_PROFILE_JSON repository secret in GitHub with a valid JSON object, e.g.:\n"
            '  {"name": "Your Name", "preferences": "..."}'
        )

    try:
        profile = json.loads(raw_profile)
    except json.JSONDecodeError as e:
        sys.exit(
            f"Error parsing OWNER_PROFILE_JSON: {e}.\n"
            "Ensure OWNER_PROFILE_JSON contains a valid JSON object."
        )

    if not isinstance(profile, dict):
        sys.exit("Error: OWNER_PROFILE_JSON must be a JSON object ({...}).")

    owner = os.environ.get("OWNER_ACCOUNT_ID", "owner")

    conn = await asyncpg.connect(database_url)
    try:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS user_models (
                   session_id TEXT PRIMARY KEY,
                   data JSONB NOT NULL,
                   updated_at BIGINT NOT NULL
               )"""
        )
        # Merged over what's there, so edits made in Settings and what Sem learned (OCEAN, observed style) stay
        # unless this profile sets the same field.
        await conn.execute(
            """INSERT INTO user_models (session_id, data, updated_at)
               VALUES ($3, $1::jsonb, $2)
               ON CONFLICT (session_id) DO UPDATE SET data = user_models.data || $1::jsonb, updated_at = $2""",
            json.dumps(profile), int(time.time()), owner,
        )
    finally:
        await conn.close()

    # Keys only, never values — this log is visible in a public repo's Actions tab.
    print(f"Seeded owner profile with keys: {sorted(profile.keys())}")


asyncio.run(main())
