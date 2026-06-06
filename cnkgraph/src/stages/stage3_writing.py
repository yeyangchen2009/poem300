"""
Stage 3: Crawl writing data (writing + writing_clause + writing_comment + writing_allusion).
DB: data/cnkgraph.duckdb (unified)
"""

from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count, reset_progress, _pk_dynasty

ALL_DYNASTIES = [
    "先秦", "秦朝", "汉朝", "三国", "晋朝", "南北朝",
    "隋朝", "唐朝", "五代", "宋朝", "金朝", "元朝",
    "明朝", "清朝", "当代"
]


async def run(client, dynasty: str = None, author_id: int = None, reset: bool = False, limit: int = 0):
    if author_id and not dynasty:
        print("[writing] --author-id requires --dynasty")
        return
    if dynasty and author_id:
        await _crawl_author(client, dynasty, author_id, reset, limit)
    elif dynasty:
        await _crawl_dynasty(client, dynasty, reset, limit)
    else:
        await _crawl_all(client, reset, limit)


async def _crawl_all(client, reset: bool, limit: int = 0):
    print("[writing] Fetching dynasty overview...")
    data = await client.get("/writing")
    if not data:
        print("[writing] Failed to fetch overview.")
        return

    api_dynasties = data.get("Dynasties", [])
    print(f"[writing] API reports {len(api_dynasties)} dynasties:")
    for d in api_dynasties:
        print(f"  {d.get('Name', '?'):8s}  {d.get('AuthorCount', 0):>6,} authors  {d.get('WritingCount', 0):>8,} writings")

    for dyn_info in api_dynasties:
        dyn_name = dyn_info.get("Name", "")
        if dyn_name:
            await _crawl_dynasty(client, dyn_name, reset, limit)


async def _crawl_dynasty(client, dynasty: str, reset: bool, limit: int = 0):
    pcon = get_progress_db()
    con = get_db()

    try:
        progress = get_progress(pcon, "writing", dynasty=dynasty)
        if progress and progress["status"] == "done" and not reset:
            print(f"[writing:{dynasty}] Already done, skipping.")
            return

        if reset:
            reset_progress(pcon, "writing", dynasty)

        print(f"[writing:{dynasty}] Fetching author list...")
        data = await client.get(f"/writing/{dynasty}")
        if not data:
            print(f"[writing:{dynasty}] Failed to fetch author list.")
            return

        authors_by_dynasty = data.get("AuthorsByDynasty", {})
        dynasties_data = authors_by_dynasty.get("Dynasties", [])
        all_authors = []
        for sub_dyn in dynasties_data:
            for author in (sub_dyn.get("Authors") or []):
                all_authors.append(author)
        print(f"[writing:{dynasty}] Found {len(all_authors)} authors")

        if limit:
            all_authors = all_authors[:limit]
            print(f"[writing:{dynasty}] Limited to {len(all_authors)} authors")

        total_writings = 0
        for i, author in enumerate(all_authors):
            aid = author.get("Id")
            aname = author.get("Name", "")
            wcount = author.get("WritingCount", 0)
            if not aid:
                continue

            author_progress = get_progress(pcon, "writing", dynasty=dynasty, author_id=aid)
            if author_progress and author_progress["status"] == "done" and not reset:
                continue

            writing_types = ["Poem"]
            total_pages = 0
            for wtype in writing_types:
                pages, writings_count = await _crawl_author_type(con, pcon, client, dynasty, aname, aid, wtype, limit, total_writings)
                total_pages += pages
                total_writings += writings_count

            upsert_progress(pcon, "writing", dynasty, aid, 0, "done", wcount)
            print(f"[writing:{dynasty}] Author {i+1}/{len(all_authors)}: {aname} ({wcount} writings, {total_pages} pages)")

            if limit and total_writings >= limit:
                print(f"[writing:{dynasty}] Reached limit of {limit} writings")
                break

            if client.should_abort:
                print(f"[writing:{dynasty}] Too many failures, stopping.")
                return

        upsert_progress(pcon, "writing", dynasty, None, 0, "done", 0)
        total = get_row_count(con, "writing")
        print(f"[writing:{dynasty}] Done. Total writings in DB: {total:,}")
    finally:
        con.close()
        pcon.close()


async def _crawl_author(client, dynasty: str, author_id: int, reset: bool, limit: int = 0):
    pcon = get_progress_db()
    con = get_db()

    try:
        progress = get_progress(pcon, "writing", dynasty=dynasty, author_id=author_id)
        if progress and progress["status"] == "done" and not reset:
            print(f"[writing:{dynasty}:author={author_id}] Already done, skipping.")
            return
        if reset:
            pcon.execute("DELETE FROM crawl_progress WHERE module = 'writing' AND dynasty = ? AND author_id = ?",
                        [_pk_dynasty(dynasty), author_id])

        row = con.execute("SELECT author_name FROM writing WHERE author_id = ? LIMIT 1", [author_id]).fetchone()
        author_name = row[0] if row else str(author_id)
        print(f"[writing:{dynasty}] Crawling author: {author_name} (ID: {author_id})")

        await _crawl_author_type(con, pcon, client, dynasty, author_name, author_id, "Poem", limit)
        upsert_progress(pcon, "writing", dynasty, author_id, 0, "done", 0)
        print(f"[writing:{dynasty}] Author {author_name} done.")
    finally:
        con.close()
        pcon.close()


async def _crawl_author_type(con, pcon, client, dynasty: str, author_name: str,
                              author_id: int, writing_type: str,
                              limit: int = 0, already_written: int = 0) -> tuple:
    name_segment = author_name[0] if author_name else "X"
    page_no = 0
    pages_crawled = 0
    writings_written = 0

    progress = get_progress(pcon, "writing", dynasty=dynasty, author_id=author_id)
    if progress and progress["status"] == "in_progress":
        page_no = progress["page_no"]
        if page_no > 0:
            print(f"  Resuming {author_name} from page {page_no}")

    while True:
        if client.should_abort:
            return pages_crawled, writings_written

        data = await client.get(
            f"/writing/{dynasty}/{name_segment}/{author_id}/{writing_type}",
            params={"pageNo": page_no}
        )
        if not data:
            print(f"  [WARN] No data for {author_name} page {page_no}")
            break

        writings = data.get("Writings", [])
        if not writings:
            break

        remaining = None
        if limit:
            remaining = limit - already_written - writings_written
            if remaining <= 0:
                break
            if remaining < len(writings):
                writings = writings[:remaining]

        _write_writings(con, writings)
        writings_written += len(writings)
        pages_crawled += 1
        page_size = data.get("PageSize", 20)

        if page_no % 10 == 0:
            print(f"  {author_name} page {page_no}: {len(writings)} writings")

        if pages_crawled % 5 == 0:
            upsert_progress(pcon, "writing", dynasty, author_id, page_no + 1, "in_progress", page_no * page_size)

        if len(writings) < page_size:
            break
        if limit and already_written + writings_written >= limit:
            break
        page_no += 1

    return pages_crawled, writings_written


def _write_writings(con, writings: list):
    for w in writings:
        wid = w.get("Id")
        if not wid:
            continue

        title_obj = w.get("Title", {})
        title = title_obj.get("Content", "") if isinstance(title_obj, dict) else str(title_obj)

        con.execute("""
            INSERT INTO writing (id, author_id, author_name, title, dynasty,
                author_date_raw, author_place_raw, writing_type, type_detail,
                rhyme, first_clause_rhyme, rank, preface, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title, author_date_raw = EXCLUDED.author_date_raw,
                author_place_raw = EXCLUDED.author_place_raw
        """, [wid, w.get("AuthorId"), w.get("Author", ""), title,
              w.get("Dynasty"), w.get("AuthorDate"), w.get("AuthorPlace"),
              w.get("Type"), w.get("TypeDetail"), w.get("Rhyme"),
              w.get("FirstClauseRhyme"), w.get("Rank", 0), w.get("Preface"), w.get("Note")])

        for idx, clause in enumerate(w.get("Clauses") or []):
            clause_content = clause.get("Content", "") if isinstance(clause, dict) else str(clause)
            rhyme_char = clause.get("RhymeChar") if isinstance(clause, dict) else None
            con.execute("""
                INSERT INTO writing_clause (writing_id, idx, content, rhyme_char)
                VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
            """, [wid, idx, clause_content, rhyme_char])

        for comment in (w.get("Comments") or []):
            con.execute("""
                INSERT INTO writing_comment (writing_id, book, section, content, full_path)
                VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
            """, [wid, comment.get("Book") or "", comment.get("Section") or "",
                  comment.get("Content") or "", comment.get("FullPath") or ""])

        for allusion in (w.get("Allusions") or []):
            con.execute("""
                INSERT INTO writing_allusion (writing_id, allusion_index, allusion_key, sentence_index)
                VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
            """, [wid, allusion.get("Index"), allusion.get("Key"), allusion.get("SentenceIndex")])
