import asyncio
import json
import os
import sys
import time

import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.passphrase import hash_passphrase  # noqa: E402


async def main():
    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        sys.exit("Error: NEON_DATABASE_URL environment variable is not set.")

    raw_accounts = os.environ.get("OWNER_ACCOUNTS_JSON", "").strip()
    if not raw_accounts:
        sys.exit(
            "Error: OWNER_ACCOUNTS_JSON environment variable (or repository secret) is empty or not set.\n"
            "Please configure the OWNER_ACCOUNTS_JSON repository secret in GitHub with a valid JSON array, e.g.:\n"
            '  [{"id": "owner", "passphrase": "your-passphrase", "role": "owner"}]'
        )

    try:
        accounts = json.loads(raw_accounts)
    except json.JSONDecodeError as e:
        sys.exit(
            f"Error parsing OWNER_ACCOUNTS_JSON: {e}.\n"
            "Ensure OWNER_ACCOUNTS_JSON contains a valid JSON array."
        )

    if not isinstance(accounts, list):
        sys.exit("Error: OWNER_ACCOUNTS_JSON must be a JSON array ([{...}]).")

    conn = await asyncpg.connect(database_url)
    try:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
                   id TEXT PRIMARY KEY,
                   passphrase_hash TEXT NOT NULL,
                   role TEXT NOT NULL DEFAULT 'owner',
                   created_at BIGINT NOT NULL
               )"""
        )
        # Re-seeding rotates passphrases: bumping token_version signs out old logins and MCP keys (as a reset does).
        await conn.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0")
        for account in accounts:
            passphrase_hash = hash_passphrase(account["passphrase"])
            await conn.execute(
                """INSERT INTO accounts (id, passphrase_hash, role, created_at)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (id) DO UPDATE SET passphrase_hash=$2, role=$3,
                       token_version = COALESCE(accounts.token_version, 0) + 1""",
                account["id"], passphrase_hash, account.get("role", "owner"), int(time.time()),
            )
    finally:
        await conn.close()

    # IDs and roles only, never the passphrase — this log is visible in a public repo's Actions tab.
    print(f"Seeded accounts: {[(a['id'], a.get('role', 'owner')) for a in accounts]}")


asyncio.run(main())
