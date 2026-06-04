"""
Crawl non-Tang poets from 卷11 小学生古诗词 and their writings.
Only runs Stage 2 (people) and Stage 3 (writings) — the other 7 tables
(dynasty, era_year, region, region_history, rhyme_entry, ci_tune, qu_tune)
are shared and already fully crawled by crawl-tang300.py.

Usage:
    python src/crawl-juan11.py                  # full run
    python src/crawl-juan11.py --skip-stage 2   # skip people, only writings
    python src/crawl-juan11.py --concurrency 2  # higher concurrency
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from api import CnkgraphClient
from db import get_db, get_progress_db, get_progress, upsert_progress

# 卷11 非唐朝诗人，按朝代分组
# 北朝民歌：cnkgraph 无条目，排除
# 陶渊明→陶潜: cnkgraph 用本名"陶潜"，"陶渊明"是别名
JUAN11_POETS = {
    "汉朝": ["项羽"],
    "三国": ["曹植"],
    "晋朝": ["陶潜"],
    "宋朝": ["苏轼", "王安石", "杨万里", "李清照", "陆游", "辛弃疾", "范仲淹", "曾巩", "文天祥"],
    "明朝": ["唐寅", "于谦"],
    "清朝": ["郑燮", "袁枚", "龚自珍", "纳兰性德"],
}


async def resolve_poet_ids(client) -> dict:
    """Resolve poet IDs from each dynasty's people list."""
    print("[juan11] Resolving poet IDs...")
    id_map = {}

    for dynasty, names in JUAN11_POETS.items():
        poet_set = set(names)
        print(f"[juan11] Fetching {dynasty} people list ({len(names)} poets)...")

        data = await client.get(f"/people/{dynasty}", timeout=120)
        if not data:
            print(f"[juan11] Failed to fetch {dynasty} people list, retrying...")
            data = await client.get(f"/people/{dynasty}", timeout=180)
        if not data:
            print(f"[juan11] Failed to fetch {dynasty} after 2 attempts.")
            continue

        people = data.get("People", [])
        matched = 0
        for p in people:
            name = p.get("Name", "")
            if name in poet_set:
                id_map[name] = (p.get("Id"), dynasty)
                matched += 1

        unmatched = poet_set - {n for n, _ in [(k, v) for k, v in id_map.items() if id_map.get(k, (None, dynasty))[1] == dynasty]}
        print(f"[juan11] {dynasty}: matched {matched}/{len(names)}")
        if unmatched:
            print(f"[juan11] {dynasty} unmatched: {', '.join(sorted(unmatched))}")

    print(f"[juan11] Total matched: {len(id_map)}/{sum(len(v) for v in JUAN11_POETS.values())}")
    return id_map


async def crawl_people(client, id_map: dict):
    """Stage 2: crawl people details for each poet."""
    print("\n=== Stage 2: People ===")
    pcon = get_progress_db()
    con = get_db(2)
    try:
        progress = get_progress(pcon, "juan11_people")
        if progress and progress["status"] == "done":
            print("[people] Already done, skipping.")
            return

        written = 0
        detail_count = 0
        for name, (pid, dynasty) in id_map.items():
            if not pid:
                continue

            detail = await client.get(f"/people/{pid}")
            if not detail:
                print(f"[people] Failed to fetch detail for {name}")
                continue

            person_obj = detail.get("Person", {})
            profile = person_obj.get("Profile", {})

            con.execute("""
                INSERT INTO person (id, name, surname, dynasty, birth_year, death_year, birth_day, death_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name, surname = EXCLUDED.surname, dynasty = EXCLUDED.dynasty,
                    birth_year = EXCLUDED.birth_year, death_year = EXCLUDED.death_year
            """, [pid, name, person_obj.get("Surname"), dynasty,
                  str(profile.get("BirthYear", "")) if profile.get("BirthYear") else None,
                  str(profile.get("DeathYear", "")) if profile.get("DeathYear") else None,
                  profile.get("BirthDay"), profile.get("DeathDay")])

            for alias in (profile.get("Aliases") or []):
                con.execute("""
                    INSERT INTO person_alias (person_id, name, type, source)
                    VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
                """, [pid, alias.get("Name", ""), alias.get("Type", ""), alias.get("Source")])

            for ht in (profile.get("Hometown") or []):
                con.execute("""
                    INSERT INTO person_hometown (person_id, region_id, name)
                    VALUES (?, ?, ?) ON CONFLICT DO NOTHING
                """, [pid, ht.get("RegionId"), ht.get("Name")])

            for det in (person_obj.get("Details") or []):
                con.execute("""
                    INSERT INTO person_detail (person_id, book, content, is_review)
                    VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
                """, [pid, det.get("Book") or "", det.get("Content") or "", det.get("IsReview", False)])
                detail_count += 1

            written += 1
            print(f"[people] {written}/{len(id_map)}: {name} ({dynasty})")

        upsert_progress(pcon, "juan11_people", None, None, 0, "done", written)
        print(f"[people] Done: {written} poets, {detail_count} details")
    finally:
        con.close()
        pcon.close()


async def crawl_writings(client, id_map: dict):
    """Stage 3: crawl writings for each poet."""
    print("\n=== Stage 3: Writings ===")
    con = get_db(3)
    try:
        total_writings = 0
        for i, (name, (pid, dynasty)) in enumerate(id_map.items()):
            if not pid:
                continue
            name_segment = name[0] if name else "X"
            page_no = 0
            pages = 0
            while True:
                data = await client.get(
                    f"/writing/{dynasty}/{name_segment}/{pid}/Poem",
                    params={"pageNo": page_no}
                )
                if not data:
                    break
                writings = data.get("Writings", [])
                if not writings:
                    break

                from stages.stage3_writing import _write_writings
                _write_writings(con, writings)
                total_writings += len(writings)
                pages += 1

                page_size = data.get("PageSize", 20)
                if len(writings) < page_size:
                    break
                page_no += 1

            if pages > 0:
                print(f"[writings] {name} ({dynasty}): {total_writings} cumulative ({pages} pages)")

            if client.should_abort:
                print("[writings] Too many failures, stopping.")
                break

        print(f"[writings] Done: {total_writings} total writings")
    finally:
        con.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crawl 卷11 non-Tang poets from cnkgraph")
    parser.add_argument("--skip-stage", type=int, action="append", default=[],
                        help="Skip a stage (e.g. --skip-stage 2)")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Concurrency (default 1)")
    args = parser.parse_args()

    skip = set(args.skip_stage)
    client = CnkgraphClient(concurrency=args.concurrency)

    try:
        id_map = await resolve_poet_ids(client)
        if not id_map:
            print("[juan11] No poets matched, aborting.")
            return

        if 2 not in skip:
            await crawl_people(client, id_map)
        else:
            print("[Stage 2] Skipped")

        if 3 not in skip:
            await crawl_writings(client, id_map)
        else:
            print("[Stage 3] Skipped")

        print("\n=== Done ===")
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
