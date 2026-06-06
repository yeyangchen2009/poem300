"""
Stage 2: Crawl people data (person + person_alias + person_hometown + person_detail).
DB: data/cnkgraph.duckdb (unified)
"""

from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count, reset_progress

ALL_DYNASTIES = [
    "先秦", "秦朝", "汉朝", "三国", "晋朝", "南北朝",
    "隋朝", "唐朝", "五代", "宋朝", "金朝", "元朝",
    "明朝", "清朝", "当代"
]


async def run(client, dynasty: str = None, reset: bool = False, limit: int = 0):
    dynasties = [dynasty] if dynasty else ALL_DYNASTIES
    for dyn in dynasties:
        await _crawl_dynasty(client, dyn, reset, limit)


async def _crawl_dynasty(client, dynasty: str, reset: bool, limit: int = 0):
    pcon = get_progress_db()
    con = get_db()

    try:
        progress = get_progress(pcon, "people", dynasty=dynasty)
        if progress and progress["status"] == "done" and not reset:
            print(f"[people:{dynasty}] Already done, skipping.")
            return

        if reset:
            reset_progress(pcon, "people", dynasty)

        print(f"[people:{dynasty}] Fetching people list...")
        data = await client.get(f"/people/{dynasty}")
        if not data:
            print(f"[people:{dynasty}] Failed to fetch list.")
            return

        people = data.get("People", [])
        print(f"[people:{dynasty}] Found {len(people)} people")

        if not people:
            upsert_progress(pcon, "people", dynasty, None, 0, "done", 0)
            return

        if limit:
            people = people[:limit]
            print(f"[people:{dynasty}] Limited to {len(people)} people")

        written = 0
        for p in people:
            pid = p.get("Id")
            if not pid:
                continue
            con.execute("""
                INSERT INTO person (id, name, surname, dynasty, birth_year, death_year, birth_day, death_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name, surname = EXCLUDED.surname, dynasty = EXCLUDED.dynasty,
                    birth_year = EXCLUDED.birth_year, death_year = EXCLUDED.death_year
            """, [pid, p.get("Name", ""), p.get("Surname"), p.get("Dynasty"),
                  str(p.get("BirthYear", "")) if p.get("BirthYear") else None,
                  str(p.get("DeathYear", "")) if p.get("DeathYear") else None,
                  p.get("BirthDay"), p.get("DeathDay")])

            for alias in (p.get("Aliases") or []):
                con.execute("""
                    INSERT INTO person_alias (person_id, name, type, source)
                    VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
                """, [pid, alias.get("Name", ""), alias.get("Type", ""), alias.get("Source")])

            for ht in (p.get("Hometown") or []):
                con.execute("""
                    INSERT INTO person_hometown (person_id, region_id, name)
                    VALUES (?, ?, ?) ON CONFLICT DO NOTHING
                """, [pid, ht.get("RegionId"), ht.get("Name")])

            written += 1
            if written % 200 == 0:
                print(f"[people:{dynasty}] {written}/{len(people)} people written...")
                upsert_progress(pcon, "people", dynasty, None, 0, "in_progress", written)

        # Fetch details for each person
        print(f"[people:{dynasty}] Fetching details for {len(people)} people...")
        detail_count = 0
        for i, p in enumerate(people):
            pid = p.get("Id")
            if not pid:
                continue
            if client.should_abort:
                print(f"[people:{dynasty}] Too many failures, stopping.")
                upsert_progress(pcon, "people", dynasty, None, i, "in_progress", written)
                return

            detail_data = await client.get(f"/people/{pid}")
            if not detail_data:
                continue

            person_obj = detail_data.get("Person", {})
            profile = person_obj.get("Profile", {})
            if profile:
                con.execute("""
                    UPDATE person SET birth_day = COALESCE(?, birth_day), death_day = COALESCE(?, death_day)
                    WHERE id = ?
                """, [profile.get("BirthDay"), profile.get("DeathDay"), pid])
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

            if (i + 1) % 100 == 0:
                print(f"[people:{dynasty}] Details: {i+1}/{len(people)}")
                upsert_progress(pcon, "people", dynasty, None, i + 1, "in_progress", written)

        upsert_progress(pcon, "people", dynasty, None, 0, "done", written)
        print(f"[people:{dynasty}] Done: {written} people, {detail_count} details. Total: {get_row_count(con, 'person'):,}")
    finally:
        con.close()
        pcon.close()
