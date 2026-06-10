"""
Stage 1: Crawl calendar data (dynasty + king + era_year + ganzhi_year + date_parse + date_link).
DB: data/cnkgraph.duckdb (unified)

API endpoints:
  GET /api/calendar                         → { Dynasties: [{Name, BeginYear, EndYear, SubDynasties}] }
  GET /api/calendar/{dynasty}               → { Dynasties: [{Kings: [{Id, Name, EraYears}]}] }
  GET /api/calendar/GanZhi/{key}            → { GanZhi, Years: [{Year, LinkCount}] }
  GET /api/calendar/Date/{key}              → { Key, Year, YearGanZhi, Month, Day, DayGanZhi, EraName, EraId, LinkCount }
  GET /api/calendar/Date/{key}/Links        → [{ LabelType, LabelIdentity, ResourceType, ResourceId, Value, Start, Length, Weight }]
"""

import json
from urllib.parse import quote
from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count
import re

# 60 heavenly stems + earthly branches combinations
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

GANZHI_60 = []
for i in range(60):
    GANZHI_60.append(HEAVENLY_STEMS[i % 10] + EARTHLY_BRANCHES[i % 12])


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


async def run(client, limit: int = 0, dynasty: str = None, author_id: int = None, reset: bool = False):
    con = get_db()
    pcon = con

    try:
        # --- Dynasty + King + EraYear (always crawl all — only ~20 dynasties, very fast) ---
        progress = get_progress(pcon, "calendar")
        if progress and progress["status"] == "done" and not reset:
            print("[calendar] Already done, skipping dynasty/era_year.")
        else:
            await _crawl_dynasties(con, pcon, client, None, limit)

        # --- GanZhi years (skip if already done) ---
        gz_progress = get_progress(pcon, "ganzhi_year")
        if gz_progress and gz_progress["status"] == "done" and not reset:
            print("[calendar] GanZhi already done, skipping.")
        else:
            await _crawl_ganzhi(con, pcon, client, limit)

        # --- Date parse + links (for author-specific dates) ---
        if author_id:
            await _crawl_author_dates(con, pcon, client, author_id, limit)

        print(f"[calendar] Done: {get_row_count(con, 'dynasty')} dynasties, "
              f"{get_row_count(con, 'king')} kings, {get_row_count(con, 'era_year')} era_years, "
              f"{get_row_count(con, 'ganzhi_year')} ganzhi_years, "
              f"{get_row_count(con, 'date_parse')} date_parses, "
              f"{get_row_count(con, 'date_link')} date_links")
    finally:
        con.commit(); con.close()


async def _crawl_dynasties(con, pcon, client, dynasty: str = None, limit: int = 0):
    print("[calendar] Fetching dynasty list...")
    data = await client.get("/calendar")
    if not data:
        print("[calendar] Failed to fetch /api/calendar")
        return

    dynasties = data.get("Dynasties", [])
    print(f"[calendar] Found {len(dynasties)} dynasties")

    if dynasty:
        dynasties = [d for d in dynasties if d.get("Name") == dynasty]
        if not dynasties:
            all_data = await client.get("/calendar")
            for d in (all_data.get("Dynasties", []) if all_data else []):
                for sub in (d.get("SubDynasties") or []):
                    if sub.get("Name") == dynasty:
                        dynasties = [d]
                        break
        print(f"[calendar] Filtered to dynasty: {dynasty} ({len(dynasties)} matched)")

    # Write dynasty rows
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

    # Fetch details: kings + era_years
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
            dyn_name = sub_dyn.get("Name") or name
            for king in (sub_dyn.get("Kings") or []):
                # Write king
                kid = king.get("Id")
                if kid and dyn_name:
                    con.execute("""
                        INSERT INTO king (id, name, dynasty, govern_begin, govern_end, author_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """, [kid, king.get("Name", ""), dyn_name,
                          king.get("GovernBegin"), king.get("GovernEnd"),
                          king.get("AuthorId")])

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


async def _crawl_ganzhi(con, pcon, client, limit: int = 0):
    print(f"[calendar] Crawling GanZhi years ({len(GANZHI_60)} combinations)...")
    total = 0
    for i, gz in enumerate(GANZHI_60):
        if client.should_abort:
            break
        data = await client.get(f"/calendar/GanZhi/{gz}")
        if not data:
            continue

        years = data.get("Years", [])
        for y in years:
            year_val = y.get("Year")
            if year_val is None:
                continue
            con.execute("""
                INSERT INTO ganzhi_year (ganzhi, year, link_count)
                VALUES (?, ?, ?) ON CONFLICT DO NOTHING
            """, [gz, year_val, y.get("LinkCount", 0)])
            total += 1

        if (i + 1) % 10 == 0:
            print(f"[calendar] GanZhi: {i+1}/{len(GANZHI_60)}, {total} entries")
            upsert_progress(pcon, "ganzhi_year", None, None, i + 1, "in_progress", total)

        if limit and total >= limit:
            print(f"[calendar] GanZhi reached limit of {limit}")
            break

    upsert_progress(pcon, "ganzhi_year", None, None, 0, "done", total)
    print(f"[calendar] GanZhi done: {total:,} entries")


async def _crawl_author_dates(con, pcon, client, author_id: int, limit: int = 0):
    """Crawl date_parse and date_link for dates mentioned in an author's writings."""
    # Collect date strings from writing.author_date_raw
    date_keys = [r[0] for r in con.execute(
        "SELECT DISTINCT author_date_raw FROM writing "
        "WHERE author_id = ? AND author_date_raw IS NOT NULL AND author_date_raw != ''",
        [author_id]
    ).fetchall()]

    if not date_keys:
        print(f"[calendar:{author_id}] No date strings found in writings.")
        return

    print(f"[calendar:{author_id}] Found {len(date_keys)} unique date strings")

    parse_count = 0
    link_count = 0
    for key in date_keys:
        if client.should_abort:
            break
        if limit and parse_count >= limit:
            break

        # Parse date — URL-encode the Chinese date string
        data = await client.get(f"/calendar/Date/{quote(key, safe='')}")
        if not data:
            continue

        con.execute("""
            INSERT INTO date_parse (input_key, year, year_ganzhi, month, day, day_ganzhi, era_name, era_id, link_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (input_key) DO NOTHING
        """, [key, str(data.get("Year", "")) if data.get("Year") else None,
              data.get("YearGanZhi"), str(data.get("Month", "")) if data.get("Month") else None,
              str(data.get("Day", "")) if data.get("Day") else None,
              data.get("DayGanZhi"), data.get("EraName"), data.get("EraId"),
              data.get("LinkCount", 0)])
        parse_count += 1

        # Fetch links for this date
        link_data = await client.get(f"/calendar/Date/{quote(key, safe='')}/Links")
        if link_data and isinstance(link_data, list):
            for link in link_data:
                con.execute("""
                    INSERT INTO date_link (input_key, label_type, label_identity, resource_type,
                                           resource_id, value, start, length, weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                """, [key, link.get("LabelType"), link.get("LabelIdentity"),
                      link.get("ResourceType"), link.get("ResourceId"),
                      link.get("Value"), link.get("Start"), link.get("Length"),
                      link.get("Weight", 0)])
                link_count += 1

    print(f"[calendar:{author_id}] Date parse: {parse_count} parsed, {link_count} links")
