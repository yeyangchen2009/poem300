"""
Stage 2: Crawl people data (person + person_alias + person_hometown + person_detail
          + biography_activity + mentionship + mentionship_writing).
DB: data/cnkgraph.duckdb (unified)
"""

import json
from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count, reset_progress

ALL_DYNASTIES = [
    "先秦", "秦朝", "汉朝", "三国", "晋朝", "南北朝",
    "隋朝", "唐朝", "五代", "宋朝", "金朝", "元朝",
    "明朝", "清朝", "当代"
]


async def run(client, dynasty: str = None, reset: bool = False, limit: int = 0,
              author_id: int = None):
    if author_id:
        await _crawl_single_person(client, author_id, reset)
    else:
        dynasties = [dynasty] if dynasty else ALL_DYNASTIES
        for dyn in dynasties:
            await _crawl_dynasty(client, dyn, reset, limit)


async def _crawl_single_person(client, author_id: int, reset: bool = False):
    """Crawl all data for a single person by ID."""
    con = get_db()
    pcon = con

    try:
        progress = get_progress(pcon, "people", dynasty="__SINGLE__", author_id=author_id)
        if progress and progress["status"] == "done" and not reset:
            print(f"[people:{author_id}] Already done, skipping.")
            return

        print(f"[people:{author_id}] Fetching person profile...")
        data = await client.get(f"/people/{author_id}")
        if not data:
            print(f"[people:{author_id}] Failed to fetch profile.")
            return

        person_obj = data.get("Person", {})
        profile = person_obj.get("Profile", {})

        if not profile:
            print(f"[people:{author_id}] No profile found.")
            return

        pid = profile.get("Id", author_id)
        name = profile.get("Name", "")
        dynasty = profile.get("Dynasty", "")

        # Write person (skip if already exists — DuckDB FK constraints block UPDATE on referenced rows)
        existing = con.execute("SELECT id FROM person WHERE id = ?", [pid]).fetchone()
        if not existing:
            con.execute("""
                INSERT INTO person (id, name, surname, dynasty, birth_year, death_year, birth_day, death_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [pid, name, profile.get("Surname"), dynasty,
                  str(profile.get("BirthYear", "")) if profile.get("BirthYear") else None,
                  str(profile.get("DeathYear", "")) if profile.get("DeathYear") else None,
                  profile.get("BirthDay"), profile.get("DeathDay")])

        # Write aliases
        for alias in (profile.get("Aliases") or []):
            con.execute("""
                INSERT INTO person_alias (person_id, name, type, source)
                VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
            """, [pid, alias.get("Name", ""), alias.get("Type", ""), alias.get("Source")])

        # Write hometowns
        for ht in (profile.get("Hometown") or []):
            con.execute("""
                INSERT INTO person_hometown (person_id, region_id, name)
                VALUES (?, ?, ?) ON CONFLICT DO NOTHING
            """, [pid, ht.get("RegionId"), ht.get("Name")])

        # Write details
        detail_count = 0
        for det in (person_obj.get("Details") or []):
            con.execute("""
                INSERT INTO person_detail (person_id, book, content, is_review)
                VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
            """, [pid, det.get("Book", ""), det.get("Content", ""), det.get("IsReview", False)])
            detail_count += 1

        print(f"[people:{author_id}] Profile: {name} ({dynasty}), "
              f"{detail_count} details, aliases/hometowns written")

        # Fetch biography activities
        # Swagger: GET /api/Biography?Author={name} → TravelTraceData {Common:TravelTrace, Traces:[TravelTrace]}
        # TravelTrace has Markers[], each Marker has Activities[]
        # Activities may be in Common (single) OR Traces (array) — must check both
        print(f"[people:{author_id}] Fetching biography...")
        bio_data = await client.get("/biography", params={"Author": name})
        bio_count = 0
        if bio_data and isinstance(bio_data, dict):
            # Collect traces from both Common and Traces
            all_traces = []
            common = bio_data.get("Common")
            if common and isinstance(common, dict):
                all_traces.append(common)
            all_traces.extend(bio_data.get("Traces", []))
            for trace in all_traces:
                for marker in (trace.get("Markers") or []):
                    for act in (marker.get("Activities") or []):
                        if isinstance(act, dict):
                            place = act.get("Place") or {}
                            people = act.get("People") or []
                            con.execute("""
                                INSERT INTO biography_activity
                                    (person_id, year, date_text, place_region_id, place_detail,
                                     title, activity, related_people, from_book, raw_json)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                            """, [pid, act.get("Year"), act.get("Date"),
                                  place.get("RegionId"), place.get("Detail") or place.get("Name"),
                                  act.get("Title"), act.get("Activity"),
                                  json.dumps(people, ensure_ascii=False) if people else None,
                                  act.get("FromBook"),
                                  json.dumps(act, ensure_ascii=False)])
                            bio_count += 1
            print(f"[people:{author_id}] Biography: {bio_count} activities (from {len(all_traces)} traces, Common={'yes' if common else 'no'})")

        # Fetch mentionship
        # API returns {Mentionship: {SourceToTarget: [{PersonId, Name, ...}], TargetToSource: [...]}}
        print(f"[people:{author_id}] Fetching mentionship...")
        men_data = await client.get(f"/people/{pid}/mentionship")
        men_count = 0
        men_writing_count = 0
        if men_data and isinstance(men_data, dict):
            men_obj = men_data.get("Mentionship", {})
            for direction, key in [("source_to_target", "SourceToTarget"), ("target_to_source", "TargetToSource")]:
                for item in (men_obj.get(key) or []):
                    tid = item.get("PersonId") or item.get("Id")
                    tname = item.get("Name", "")
                    if not tid:
                        continue
                    con.execute("""
                        INSERT INTO mentionship (person_id, target_id, target_name, direction)
                        VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [pid, tid, tname, direction])
                    men_count += 1

            # Fetch writings for first few targets only (most return 404)
            all_targets = []
            for direction, key in [("source_to_target", "SourceToTarget"), ("target_to_source", "TargetToSource")]:
                for item in (men_obj.get(key) or []):
                    tid = item.get("PersonId") or item.get("Id")
                    if tid:
                        all_targets.append(tid)
            for tid in all_targets[:10]:
                mw_data = await client.get(f"/people/{pid}/mentionship/{tid}")
                if mw_data and isinstance(mw_data, dict):
                    # Swagger: MentionshipWritingListResponse → MentionshipData → MentionshipWritingPageDto → Writings[]
                    mw_page = mw_data.get("MentionshipData", mw_data)
                    mwritings = mw_page.get("Writings", []) if isinstance(mw_page, dict) else []
                    for w in mwritings:
                        wid = w.get("Id") or w.get("WritingId")
                        if wid:
                            con.execute("""
                                INSERT INTO mentionship_writing (person_id, target_id, writing_id)
                                VALUES (?, ?, ?) ON CONFLICT DO NOTHING
                            """, [pid, tid, wid])
                            men_writing_count += 1

            print(f"[people:{author_id}] Mentionship: {men_count} targets, {men_writing_count} writings")

        upsert_progress(pcon, "people", "__SINGLE__", author_id, 0, "done",
                        1 + detail_count + bio_count + men_count)
        print(f"[people:{author_id}] Done.")
    finally:
        con.commit(); con.close()


async def _crawl_dynasty(client, dynasty: str, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con

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
        con.commit(); con.close()
