"""
Crawl only the 77 poets from 唐诗三百首 and their writings.
Runs all 5 stages but limited to Tang dynasty and these specific poets.

Usage:
    python src/crawl-tang300.py                  # full run
    python src/crawl-tang300.py --skip-stage 1    # skip calendar (already done)
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from api import CnkgraphClient
from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count, reset_progress

# 77 poets from 唐诗三百首 (poet-bio.json)
TANG300_POETS = [
    "僧皎然", "元稹", "元结", "刘方平", "刘禹锡", "刘脊虚", "刘长卿", "卢纶",
    "司空曙", "唐玄宗", "孟浩然", "孟郊", "宋之问", "岑参", "崔曙", "崔涂",
    "崔颢", "常建", "张乔", "张九龄", "张旭", "张泌", "张祜", "张籍", "张继",
    "戴叔伦", "无名氏", "朱庆余", "权德舆", "李商隐", "李白", "李益", "李端",
    "李颀", "李频", "杜审言", "杜牧", "杜甫", "杜秋娘", "杜荀鹤", "柳中庸",
    "柳宗元", "沈佺期", "温庭筠", "王之涣", "王勃", "王建", "王昌龄", "王湾",
    "王维", "王翰", "白居易", "皇甫冉", "祖咏", "秦韬玉", "綦毋潜", "薛逢",
    "裴迪", "西鄙人", "许浑", "贺知章", "贾岛", "邱为", "郑畋", "金昌绪",
    "钱起", "陈子昂", "陈陶", "韦庄", "韦应物", "韩偓", "韩愈", "韩翃",
    "顾况", "马戴", "骆宾王", "高适",
]


async def resolve_poet_ids(client) -> dict:
    """Get author IDs for the 77 poets from cnkgraph API."""
    print("[tang300] Resolving poet IDs...")
    data = await client.get("/people/唐朝")
    if not data:
        print("[tang300] Failed to fetch Tang people list.")
        return {}

    people = data.get("People", [])
    poet_set = set(TANG300_POETS)
    id_map = {}
    for p in people:
        name = p.get("Name", "")
        if name in poet_set:
            id_map[name] = p.get("Id")
    print(f"[tang300] Matched {len(id_map)}/{len(TANG300_POETS)} poets")
    unmatched = poet_set - set(id_map.keys())
    if unmatched:
        print(f"[tang300] Unmatched: {', '.join(sorted(unmatched))}")
    return id_map


async def crawl_calendar(client):
    """Stage 1: calendar (small, just fetch all)."""
    print("\n=== Stage 1: Calendar ===")
    from stages.stage1_calendar import run
    await run(client, limit=0)


async def crawl_people(client, id_map: dict):
    """Stage 2: people - only our 77 poets."""
    print("\n=== Stage 2: People ===")
    pcon = get_progress_db()
    con = get_db(2)
    try:
        progress = get_progress(pcon, "tang300_people")
        if progress and progress["status"] == "done":
            print("[people] Already done, skipping.")
            return

        written = 0
        detail_count = 0
        for name, pid in id_map.items():
            if not pid:
                continue
            # Fetch detail for each poet
            detail = await client.get(f"/people/{pid}")
            if not detail:
                continue

            person_obj = detail.get("Person", {})
            profile = person_obj.get("Profile", {})

            con.execute("""
                INSERT INTO person (id, name, surname, dynasty, birth_year, death_year, birth_day, death_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name, surname = EXCLUDED.surname, dynasty = EXCLUDED.dynasty,
                    birth_year = EXCLUDED.birth_year, death_year = EXCLUDED.death_year
            """, [pid, name, person_obj.get("Surname"), "唐朝",
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
                """, [pid, det.get("Book", ""), det.get("Content", ""), det.get("IsReview", False)])
                detail_count += 1

            written += 1
            if written % 10 == 0:
                print(f"[people] {written}/{len(id_map)} poets")

        upsert_progress(pcon, "tang300_people", None, None, 0, "done", written)
        print(f"[people] Done: {written} poets, {detail_count} details")
    finally:
        con.close()
        pcon.close()


async def crawl_writings(client, id_map: dict):
    """Stage 3: writings for each poet."""
    print("\n=== Stage 3: Writings ===")
    con = get_db(3)
    try:
        total_writings = 0
        for i, (name, pid) in enumerate(id_map.items()):
            if not pid:
                continue
            name_segment = name[0] if name else "X"
            page_no = 0
            pages = 0
            while True:
                data = await client.get(
                    f"/writing/唐朝/{name_segment}/{pid}/Poem",
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
                print(f"[writings] {name}: {total_writings} writings ({pages} pages)")
            if (i + 1) % 10 == 0:
                print(f"[writings] Progress: {i+1}/{len(id_map)} poets")

            if client.should_abort:
                print("[writings] Too many failures, stopping.")
                break

        print(f"[writings] Done: {total_writings} total writings")
    finally:
        con.close()


async def crawl_regions(client):
    """Stage 4: regions from writing and people data."""
    print("\n=== Stage 4: Regions ===")
    from stages.stage4_region import run
    await run(client, reset=True, limit=0)


async def crawl_reference(client):
    """Stage 5: reference data (small, fetch all)."""
    print("\n=== Stage 5: Reference ===")

    # ciTune - single request
    con = get_db(5)
    try:
        data = await client.get("/ciTune")
        tunes = data if isinstance(data, list) else (data.get("CiTunes", []) if isinstance(data, dict) else [])
        for t in tunes:
            tid = t.get("Id")
            if not tid:
                continue
            content = t.get("Content", "")
            if not content:
                content = json.dumps(t, ensure_ascii=False)
            elif isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            con.execute("""
                INSERT INTO ci_tune (id, name, content) VALUES (?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
            """, [tid, t.get("Name", ""), content])
        print(f"[ciTune] {len(tunes)} tunes")
    finally:
        con.close()

    # quTune - single request
    con = get_db(5)
    try:
        data = await client.get("/quTune")
        tunes = data if isinstance(data, list) else (data.get("QuTunes", []) if isinstance(data, dict) else [])
        for t in tunes:
            tid = t.get("Id")
            if not tid:
                continue
            content = t.get("Content", "")
            if not content:
                content = json.dumps(t, ensure_ascii=False)
            elif isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            con.execute("""
                INSERT INTO qu_tune (id, name, content) VALUES (?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
            """, [tid, t.get("Name", ""), content])
        print(f"[quTune] {len(tunes)} tunes")
    finally:
        con.close()

    # Rhyme - single request per book
    con = get_db(5)
    try:
        for book_name in ["平水韵", "中华新韵"]:
            data = await client.get(f"/rhyme/{book_name}")
            if not data:
                continue
            entries = data.get("Categories", []) if isinstance(data, dict) else []
            for entry in entries:
                con.execute("""
                    INSERT INTO rhyme_entry (book, name, chars) VALUES (?, ?, ?) ON CONFLICT DO NOTHING
                """, [book_name, entry.get("Name", ""), entry.get("Chars", "")])
            print(f"[rhyme:{book_name}] {len(entries)} entries")
    finally:
        con.close()

    print("[reference] Done")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crawl cnkgraph data for 唐诗三百首")
    parser.add_argument("--skip-stage", type=int, action="append", default=[],
                        help="Skip a stage (e.g. --skip-stage 1)")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Concurrency (default 1)")
    args = parser.parse_args()

    skip = set(args.skip_stage)
    client = CnkgraphClient(concurrency=args.concurrency)

    try:
        # Stage 1: Calendar
        if 1 not in skip:
            await crawl_calendar(client)
        else:
            print("[Stage 1] Skipped")

        # Resolve poet IDs first (needed for Stage 2 & 3)
        id_map = await resolve_poet_ids(client)
        if not id_map:
            print("[tang300] No poets matched, aborting.")
            return

        # Stage 2: People
        if 2 not in skip:
            await crawl_people(client, id_map)
        else:
            print("[Stage 2] Skipped")

        # Stage 3: Writings
        if 3 not in skip:
            await crawl_writings(client, id_map)
        else:
            print("[Stage 3] Skipped")

        # Stage 4: Regions
        if 4 not in skip:
            await crawl_regions(client)
        else:
            print("[Stage 4] Skipped")

        # Stage 5: Reference
        if 5 not in skip:
            await crawl_reference(client)
        else:
            print("[Stage 5] Skipped")

        print("\n=== Done ===")
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
