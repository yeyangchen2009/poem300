"""Fix allusion keys: fetch detail API for writings with NULL allusion_key."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from db import get_db
from api import CnkgraphClient


async def fix_allusion_keys(limit: int = 0):
    con = get_db()
    client = CnkgraphClient(concurrency=1, delay=1.0)

    try:
        # Find all writings that need allusion detail
        todo_ids = [r[0] for r in con.execute(
            "SELECT DISTINCT writing_id FROM writing_allusion "
            "WHERE allusion_key IS NULL OR allusion_key = ''"
        ).fetchall()]

        # Also find writings with no allusion rows at all
        no_allusion_ids = [r[0] for r in con.execute(
            "SELECT id FROM writing "
            "WHERE id NOT IN (SELECT DISTINCT writing_id FROM writing_allusion)"
        ).fetchall()]

        todo_ids = list(set(todo_ids + no_allusion_ids))
        if limit:
            todo_ids = todo_ids[:limit]

        print(f"[allusion-fix] {len(todo_ids)} writings to check")

        updated = 0
        has_allusions = 0
        batch_size = 30

        for i, wid in enumerate(todo_ids):
            if client.should_abort:
                print(f"[allusion-fix] Aborting at {i+1}/{len(todo_ids)}")
                break

            detail = await client.get(f"/writing/{wid}")
            if not detail or not isinstance(detail, dict):
                if client._rate_limit_hits > 0:
                    print(f"  [allusion-fix] Rate limited at {i+1}, pausing 60s...")
                    await asyncio.sleep(60)
                    client._rate_limit_hits = 0
                continue

            w = detail.get("Writing", {})
            allusions = w.get("Allusions", []) if isinstance(w, dict) else []

            if allusions:
                has_allusions += 1
                # Delete old rows with NULL keys for this writing
                con.execute("DELETE FROM writing_allusion WHERE writing_id = ? AND (allusion_key IS NULL OR allusion_key = '')", [wid])
                for a in allusions:
                    con.execute("""
                        INSERT INTO writing_allusion (writing_id, allusion_index, allusion_key, sentence_index)
                        VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [wid, a.get("AllusionIndex"), a.get("AllusionKey"), a.get("SentenceIndex")])
                updated += 1

            # Progress
            if (i + 1) % 100 == 0:
                con.commit()
                print(f"[allusion-fix] {i+1}/{len(todo_ids)} processed ({updated} updated, {has_allusions} have allusions)")

            # Rate control
            if (i + 1) % batch_size == 0:
                await asyncio.sleep(30)
            else:
                await asyncio.sleep(1.5)

        con.commit()
        total_with_key = con.execute(
            "SELECT COUNT(*) FROM writing_allusion WHERE allusion_key IS NOT NULL AND allusion_key != ''"
        ).fetchone()[0]
        print(f"[allusion-fix] Done: {updated}/{len(todo_ids)} updated, {total_with_key} total rows with keys")

    finally:
        await client.close()
        con.commit()
        con.close()


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    asyncio.run(fix_allusion_keys(limit))
