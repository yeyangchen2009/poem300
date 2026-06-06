"""
Stage 1: Crawl calendar data (dynasty + era_year).
DB: data/cnkgraph.duckdb (unified)

API endpoints:
  GET /api/calendar            → { Dynasties: [{Name, BeginYear, EndYear, SubDynasties}] }
  GET /api/calendar/{dynasty}  → { Name, Dynasties: [{Name, BeginYear, EndYear, Kings: [{EraYears: [...]}]}] }
"""

from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count
import re


def _parse_year(val) -> int | None:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    s = str(val)
    neg = s.startswith("前")
    m = re.search(r'\d+', s)
    if m:
        y = int(m.group())
        return -y if neg else y
    return None


async def run(client, limit: int = 0):
    """Crawl all dynasty and era_year data."""
    pcon = get_progress_db()
    con = get_db()

    try:
        progress = get_progress(pcon, "calendar")
        if progress and progress["status"] == "done":
            print("[calendar] Already done, skipping.")
            return

        print("[calendar] Fetching dynasty list...")
        data = await client.get("/calendar")
        if not data:
            print("[calendar] Failed to fetch /api/calendar")
            return

        dynasties = data.get("Dynasties", [])
        print(f"[calendar] Found {len(dynasties)} dynasties")

        written = 0
        for d in dynasties:
            name = d.get("Name", "")
            if not name:
                continue
            con.execute(
                "INSERT INTO dynasty (name, begin_year, end_year) VALUES (?, ?, ?) "
                "ON CONFLICT (name) DO UPDATE SET begin_year = EXCLUDED.begin_year, end_year = EXCLUDED.end_year",
                [name, _parse_year(d.get("BeginYear")), _parse_year(d.get("EndYear"))]
            )
            written += 1
            for sub in (d.get("SubDynasties") or []):
                sub_name = sub.get("Name", "")
                if sub_name:
                    con.execute(
                        "INSERT INTO dynasty (name, begin_year, end_year) VALUES (?, ?, ?) "
                        "ON CONFLICT (name) DO UPDATE SET begin_year = EXCLUDED.begin_year, end_year = EXCLUDED.end_year",
                        [sub_name, _parse_year(sub.get("BeginYear")), _parse_year(sub.get("EndYear"))]
                    )
                    written += 1
        print(f"[calendar] Wrote {written} dynasties")

        total_eras = 0
        for i, d in enumerate(dynasties):
            name = d.get("Name", "")
            if not name:
                continue
            print(f"[calendar] Fetching era_years for {name} ({i+1}/{len(dynasties)})...", end=" ")
            era_data = await client.get(f"/calendar/{name}")
            if not era_data:
                print("FAILED")
                continue

            era_count = 0
            for sub_dyn in (era_data.get("Dynasties") or []):
                for king in (sub_dyn.get("Kings") or []):
                    for ey in (king.get("EraYears") or []):
                        if limit and total_eras >= limit:
                            break
                        ey_name = ey.get("Name", "")
                        if not ey_name:
                            continue
                        con.execute(
                            "INSERT INTO era_year (name, dynasty, begin_year, end_year) VALUES (?, ?, ?, ?) "
                            "ON CONFLICT (name) DO UPDATE SET dynasty = EXCLUDED.dynasty, "
                            "begin_year = EXCLUDED.begin_year, end_year = EXCLUDED.end_year",
                            [ey_name, name, _parse_year(ey.get("BeginYear")), _parse_year(ey.get("EndYear"))]
                        )
                        era_count += 1
                        total_eras += 1
                    if limit and total_eras >= limit:
                        break
                if limit and total_eras >= limit:
                    break
            print(f"{era_count} eras (total: {total_eras})")
            upsert_progress(pcon, "calendar", name, None, 0, "in_progress", total_eras)
            if limit and total_eras >= limit:
                print(f"[calendar] Reached limit of {limit} era_years")
                break

        upsert_progress(pcon, "calendar", None, None, 0, "done", total_eras)
        print(f"[calendar] Done: {get_row_count(con, 'dynasty')} dynasties, {get_row_count(con, 'era_year')} era_years")
    finally:
        con.close()
        pcon.close()
