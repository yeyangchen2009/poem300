"""Extract writing links from detail API.

Also fixes allusion keys as a side effect (since we're already calling the detail API).

Links contain: DateTime (year), Region (region_id), People, Allusion labels.
"""

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


async def extract_links(limit: int = 0):
    con = get_db()
    client = CnkgraphClient(concurrency=1, delay=1.0)

    try:
        # Get all writing IDs that don't have links yet
        todo_ids = [r[0] for r in con.execute(
            "SELECT id FROM writing "
            "WHERE id NOT IN (SELECT DISTINCT writing_id FROM writing_link) "
            "ORDER BY id"
        ).fetchall()]
        if limit:
            todo_ids = todo_ids[:limit]

        print(f"[links] {len(todo_ids)} writings to extract links from")

        total_links = 0
        total_allusions = 0
        batch_size = 30

        for i, wid in enumerate(todo_ids):
            if client.should_abort:
                print(f"[links] Aborting at {i+1}/{len(todo_ids)}")
                break

            detail = await client.get(f"/writing/{wid}")
            if not detail or not isinstance(detail, dict):
                if client._rate_limit_hits > 0:
                    print(f"  [links] Rate limited at {i+1}, pausing 60s...")
                    await asyncio.sleep(60)
                    client._rate_limit_hits = 0
                continue

            # Extract Links
            links = detail.get("Links") or []
            for link in links:
                ld = link.get("LabelData") or {}
                if not isinstance(ld, dict):
                    ld = {}
                con.execute("""
                    INSERT INTO writing_link
                        (writing_id, label_type, label_identity, value, resource_path,
                         year, month, region_id, confident_level, weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                """, [
                    wid,
                    link.get("LabelType", ""),
                    link.get("LabelIdentity", ""),
                    link.get("Value", ""),
                    link.get("ResourcePath", ""),
                    ld.get("Year"),
                    ld.get("Month"),
                    link.get("LabelIdentity") if link.get("LabelType") == "Region" else None,
                    ld.get("ConfidentLevel", 0) if isinstance(ld, dict) else 0,
                    link.get("Weight", 0),
                ])
                total_links += 1

            # Fix allusion keys as side effect
            w = detail.get("Writing", {})
            allusions = w.get("Allusions", []) if isinstance(w, dict) else []
            if allusions:
                con.execute("DELETE FROM writing_allusion WHERE writing_id = ? AND (allusion_key IS NULL OR allusion_key = '')", [wid])
                for a in allusions:
                    con.execute("""
                        INSERT INTO writing_allusion (writing_id, allusion_index, allusion_key, sentence_index)
                        VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [wid, a.get("AllusionIndex"), a.get("AllusionKey"), a.get("SentenceIndex")])
                    total_allusions += 1

            if (i + 1) % 100 == 0:
                con.commit()
                print(f"[links] {i+1}/{len(todo_ids)} — {total_links} links, {total_allusions} allusions")

            if (i + 1) % batch_size == 0:
                await asyncio.sleep(30)
            else:
                await asyncio.sleep(1.5)

        con.commit()
        link_count = con.execute("SELECT COUNT(*) FROM writing_link").fetchone()[0]
        allusion_key_count = con.execute(
            "SELECT COUNT(*) FROM writing_allusion WHERE allusion_key IS NOT NULL AND allusion_key != ''"
        ).fetchone()[0]
        print(f"[links] Done: {total_links} links inserted (total: {link_count}), "
              f"{total_allusions} allusion keys (total with keys: {allusion_key_count})")

    finally:
        await client.close()
        con.commit()
        con.close()


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    asyncio.run(extract_links(limit))
