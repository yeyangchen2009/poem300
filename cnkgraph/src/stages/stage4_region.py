"""
Stage 4: Crawl region data (region + region_history + scenery).
DB: data/cnkgraph.duckdb (unified)
"""

from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count, reset_progress


async def run(client, reset: bool = False, limit: int = 0, author_id: int = None):
    con = get_db()
    pcon = con

    try:
        progress = get_progress(pcon, "region")
        if progress and progress["status"] == "done" and not reset and not author_id:
            print("[region] Already done, skipping.")
            return
        if reset:
            reset_progress(pcon, "region")

        region_ids = set()

        # Collect region IDs from writing and person tables (same DB now)
        if author_id:
            rows = con.execute(
                "SELECT DISTINCT author_place_raw FROM writing WHERE author_id = ? AND author_place_raw IS NOT NULL",
                [author_id]).fetchall()
            for r in rows:
                if r[0] and r[0].startswith("CN"):
                    region_ids.add(r[0])

            rows = con.execute(
                "SELECT DISTINCT region_id FROM person_hometown WHERE person_id = ? AND region_id IS NOT NULL",
                [author_id]).fetchall()
            for r in rows:
                if r[0]:
                    region_ids.add(r[0])
        else:
            rows = con.execute("SELECT DISTINCT author_place_raw FROM writing WHERE author_place_raw IS NOT NULL").fetchall()
            for r in rows:
                if r[0] and r[0].startswith("CN"):
                    region_ids.add(r[0])

            rows = con.execute("SELECT DISTINCT region_id FROM person_hometown WHERE region_id IS NOT NULL").fetchall()
            for r in rows:
                if r[0]:
                    region_ids.add(r[0])

        print(f"[region] Found {len(region_ids)} unique region IDs to fetch")
        if not region_ids:
            print("[region] No region IDs found. Run stages 2 and 3 first.")
            return

        sorted_ids = sorted(region_ids)
        if limit:
            sorted_ids = sorted_ids[:limit]
            print(f"[region] Limited to {len(sorted_ids)} regions")

        done_ids = set()
        if progress and progress["status"] == "in_progress":
            rows = con.execute("SELECT id FROM region").fetchall()
            done_ids = {r[0] for r in rows}
            print(f"[region] Resuming: {len(done_ids)} already fetched")

        total = len(sorted_ids)
        fetched = len(done_ids)
        new_count = 0

        for i, rid in enumerate(sorted_ids):
            if rid in done_ids:
                continue
            if client.should_abort:
                print(f"[region] Too many failures, stopping at {i}/{total}.")
                upsert_progress(pcon, "region", None, None, i, "in_progress", fetched)
                return

            data = await client.get(f"/map/region/{rid}")
            if not data:
                continue
            if isinstance(data, list):
                for item in data:
                    _write_region(con, item)
            elif isinstance(data, dict):
                _write_region(con, data)

            fetched += 1
            new_count += 1
            if new_count % 50 == 0:
                print(f"[region] {fetched}/{total} fetched")
                upsert_progress(pcon, "region", None, None, i + 1, "in_progress", fetched)

        upsert_progress(pcon, "region", None, None, 0, "done", fetched)
        print(f"[region] Done: {get_row_count(con, 'region'):,} regions, "
              f"{get_row_count(con, 'region_history'):,} history, {get_row_count(con, 'scenery'):,} scenery")
    finally:
        con.commit(); con.close()


def _write_region(con, data: dict):
    region = data.get("Region", data)
    rid = region.get("Id")
    if not rid:
        return
    # Skip if already exists (DuckDB FK constraints block UPDATE on referenced rows)
    existing = con.execute("SELECT id FROM region WHERE id = ?", [rid]).fetchone()
    if not existing:
        con.execute("""
            INSERT INTO region (id, name, latitude, longitude, parent_id, people_count, has_child)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [rid, region.get("Name", ""), region.get("Latitude"), region.get("Longitude"),
              region.get("ParentId"), region.get("PeopleCount", 0), region.get("HasChild", False)])

    for hr in (region.get("HistoryRecords") or []):
        con.execute("""
            INSERT INTO region_history (region_id, history_id, name, new_name, type,
                begin_year, end_year, begin_reason, end_reason, belong_to, external_id, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
        """, [rid, hr.get("Id"), hr.get("Name", ""), hr.get("NewName"), hr.get("Type"),
              hr.get("BeginYear"), hr.get("EndYear"), hr.get("BeginReason"), hr.get("EndReason"),
              hr.get("BelongTo"), hr.get("ExternalId"), hr.get("Latitude"), hr.get("Longitude")])

    for sc in (region.get("Sceneries") or []):
        sc_name = sc.get("Name", "") if isinstance(sc, dict) else str(sc)
        if sc_name:
            con.execute("""
                INSERT INTO scenery (region_id, name) VALUES (?, ?) ON CONFLICT DO NOTHING
            """, [rid, sc_name])
