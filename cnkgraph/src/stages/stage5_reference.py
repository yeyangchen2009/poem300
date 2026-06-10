"""
Stage 5: Crawl reference data (book, glossary, rhyme, ci_tune, qu_tune, category, char_dict).
DB: data/cnkgraph.duckdb (unified)
"""

import json
from db import get_db, get_progress_db, get_progress, upsert_progress, get_row_count, reset_progress


async def run(client, module: str = None, reset: bool = False, limit: int = 0,
              author_id: int = None):
    if author_id:
        await _crawl_author_supplement(client, author_id, reset, limit)
        return

    modules = {
        "book": _crawl_books,
        "glossary": _crawl_glossary,
        "rhyme": _crawl_rhyme,
        "ciTune": _crawl_ci_tune,
        "quTune": _crawl_qu_tune,
        "category": _crawl_category,
        "char": _crawl_char,
    }
    if module:
        if module in modules:
            await modules[module](client, reset, limit)
        else:
            print(f"[reference] Unknown module: {module}")
    else:
        for name, func in modules.items():
            print(f"\n--- {name} ---")
            await func(client, reset, limit)


async def _crawl_author_supplement(client, author_id: int, reset: bool, limit: int):
    """Crawl supplement reference data for a specific author's writings."""
    import re
    con = get_db()

    try:
        # Get writing IDs for this author
        writing_ids = [r[0] for r in con.execute(
            "SELECT id FROM writing WHERE author_id = ?", [author_id]).fetchall()]
        if not writing_ids:
            print(f"[supplement:{author_id}] No writings found. Run stage 3 first.")
            return

        print(f"[supplement:{author_id}] Found {len(writing_ids)} writings, crawling supplement data...")
        placeholders = ",".join(["?"] * len(writing_ids))

        # 1. Allusion → glossary (allusion_key from detail API)
        allusion_keys = [r[0] for r in con.execute(
            f"SELECT DISTINCT allusion_key FROM writing_allusion "
            f"WHERE writing_id IN ({placeholders}) AND allusion_key IS NOT NULL AND allusion_key != ''",
            writing_ids).fetchall()]
        if allusion_keys:
            print(f"[supplement:{author_id}] {len(allusion_keys)} unique allusion keys")
            glossary_count = 0
            for key in allusion_keys[:50]:
                if limit and glossary_count >= limit:
                    break
                # GET /api/glossary/典故/{id} — no search/find endpoint in Swagger
                data = await client.get(f"/glossary/典故/{key}")
                if data and isinstance(data, dict):
                    gid = data.get("Id") or data.get("SourceId")
                    word = data.get("Word") or data.get("Text") or key
                    con.execute("""
                        INSERT INTO supplement_glossary (id, kind, word, original_word, spells,
                            explains, categories, count_in_writings, keys, related_persons,
                            quotes, correlations, ref_data, raw_json)
                        VALUES (?, 2, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [gid, word, data.get("OriginalWord"), data.get("Spells"),
                          data.get("Explains"), data.get("Categories"),
                          data.get("CountInWritings"), data.get("Keys"),
                          data.get("RelatedPersons"), data.get("Quotes"),
                          data.get("Correlations"), data.get("RefData"),
                          json.dumps(data, ensure_ascii=False)])
                    glossary_count += 1
            print(f"[supplement:{author_id}] Glossary: {glossary_count} entries")
        else:
            print(f"[supplement:{author_id}] No allusion keys found (run stage 3 allusion detail first)")

        # 2. Book from comments
        # Swagger: POST /api/Book/Find {Key, PageNo} → KanripoSearchResult {Result:[{Category, Books:[...]}]}
        book_names = [r[0] for r in con.execute(
            f"SELECT DISTINCT book FROM writing_comment "
            f"WHERE writing_id IN ({placeholders}) AND book IS NOT NULL AND book != ''",
            writing_ids).fetchall()]
        if book_names:
            print(f"[supplement:{author_id}] {len(book_names)} unique book names in comments")
            book_count = 0
            for bname in book_names:
                if limit and book_count >= limit:
                    break
                # Strip 《》brackets from book name for better search
                search_name = bname.strip("《》").strip()
                data = await client.post("/book/find", {"Key": search_name, "PageNo": 0})
                items = []
                if isinstance(data, dict):
                    # KanripoSearchResult.Result → [{Category, Books: [KanripoBookResult]}]
                    for cat in (data.get("Result") or []):
                        items.extend(cat.get("Books") or [])
                if items:
                    for item in items[:2]:
                        bid = item.get("Id") or item.get("BookId")
                        if bid:
                            try:
                                bid = int(bid)
                            except (ValueError, TypeError):
                                continue
                            con.execute("""
                                INSERT INTO supplement_book (id, name, author, dynasty, raw_json)
                                VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                            """, [bid, item.get("Title", item.get("Name", search_name)),
                                  item.get("Author", ""), item.get("Dynasty", ""),
                                  json.dumps(item, ensure_ascii=False)])
                            book_count += 1
            print(f"[supplement:{author_id}] Books: {book_count} entries")

        # 3. Unique chars → char dict
        char_rows = con.execute(
            f"SELECT DISTINCT content FROM writing_clause WHERE writing_id IN ({placeholders})",
            writing_ids).fetchall()
        chars = set()
        for (text,) in char_rows:
            if text:
                for ch in text:
                    if '一' <= ch <= '鿿':
                        chars.add(ch)
        if chars:
            char_list = sorted(chars)
            if limit:
                char_list = char_list[:limit]
            print(f"[supplement:{author_id}] {len(char_list)} unique chars to look up")
            char_count = 0
            for ch in char_list:
                data = await client.get(f"/char/{ch}")
                if data:
                    raw = json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
                    con.execute("""
                        INSERT INTO supplement_char (char, modern_dict, kangxi_dict, shuowen_dict, raw_json)
                        VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [ch, raw, None, None, raw])
                    char_count += 1
            print(f"[supplement:{author_id}] Chars: {char_count} entries")

        print(f"[supplement:{author_id}] Done.")
    finally:
        con.commit(); con.close()


async def _crawl_books(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        progress = get_progress(pcon, "book")
        if progress and progress["status"] == "done" and not reset:
            print("[book] Already done, skipping.")
            return
        if reset:
            reset_progress(pcon, "book")

        print("[book] Fetching book list...")
        data = await client.get("/book")
        if not data:
            print("[book] Failed.")
            return

        # API returns {Total, Categories: [{Books: [...]}]}
        books = []
        if isinstance(data, list):
            books = data
        elif isinstance(data, dict):
            for cat in (data.get("Categories") or []):
                books.extend(cat.get("Books") or [])
        print(f"[book] Found {len(books)} books")

        if limit:
            books = books[:limit]
            print(f"[book] Limited to {len(books)} books")

        for b in books:
            bid = b.get("Id")
            if not bid:
                continue
            con.execute("""
                INSERT INTO book (id, title, category, subcategory)
                VALUES (?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title
            """, [bid, b.get("Title", ""), b.get("Category"), b.get("Subcategory")])

        print("[book] Fetching volumes...")
        for i, b in enumerate(books):
            bid = b.get("Id")
            if not bid:
                continue
            if client.should_abort:
                upsert_progress(pcon, "book", None, None, i, "in_progress", i)
                return
            detail = await client.get(f"/book/{bid}")
            if not detail:
                continue
            for v in detail.get("Volumes", []):
                con.execute("""
                    INSERT INTO book_volume (id, book_id, title, content)
                    VALUES (?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
                """, [v.get("Id", ""), bid, v.get("Title", ""), v.get("Content", "")])
            if (i + 1) % 500 == 0:
                print(f"[book] {i+1}/{len(books)} processed")
                upsert_progress(pcon, "book", None, None, i + 1, "in_progress", i + 1)

        upsert_progress(pcon, "book", None, None, 0, "done", len(books))
        print(f"[book] Done: {get_row_count(con, 'book'):,} books, {get_row_count(con, 'book_volume'):,} volumes")
    finally:
        con.commit(); con.close()


GLOSSARY_TYPES = []  # API returns 405, skip glossary for now


async def _crawl_glossary(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        total_fetched = 0
        for gtype in GLOSSARY_TYPES:
            progress = get_progress(pcon, "glossary", dynasty=gtype)
            if progress and progress["status"] == "done" and not reset:
                print(f"[glossary:{gtype}] Already done.")
                continue
            if reset:
                reset_progress(pcon, "glossary", dynasty=gtype)

            print(f"[glossary:{gtype}] Fetching list...")
            data = await client.get(f"/glossary/{gtype}")
            if not data:
                print(f"[glossary:{gtype}] Failed.")
                continue

            glossaries = data.get("Glossaries", [])
            print(f"[glossary:{gtype}] Found {len(glossaries)} entries")

            if limit:
                remaining = limit - total_fetched
                if remaining <= 0:
                    break
                if remaining < len(glossaries):
                    glossaries = glossaries[:remaining]
                    print(f"[glossary:{gtype}] Limited to {len(glossaries)} entries")

            for i, g in enumerate(glossaries):
                gid = g.get("Id") or g.get("SourceId")
                if not gid:
                    continue
                detail = await client.get(f"/glossary/{gtype}/{gid}")
                if detail:
                    con.execute("""
                        INSERT INTO glossary (glossary_type, source_id, text, content, spells, traditional)
                        VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [gtype, gid, detail.get("Text", ""), detail.get("Content", ""),
                          detail.get("Spells", ""), detail.get("Traditional", "")])
                else:
                    con.execute("""
                        INSERT INTO glossary (glossary_type, source_id, text, content, spells)
                        VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
                    """, [gtype, gid, g.get("Text", ""), g.get("Content", ""), g.get("Spells", "")])
                if client.should_abort:
                    upsert_progress(pcon, "glossary", gtype, None, i, "in_progress", i)
                    return
                if (i + 1) % 200 == 0:
                    print(f"[glossary:{gtype}] {i+1}/{len(glossaries)}")

            upsert_progress(pcon, "glossary", gtype, None, 0, "done", len(glossaries))
            total_fetched += len(glossaries)
    finally:
        con.commit(); con.close()


RHYME_BOOKS = ["平水韵", "中华新韵"]


async def _crawl_rhyme(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        for book_name in RHYME_BOOKS:
            progress = get_progress(pcon, "rhyme", dynasty=book_name)
            if progress and progress["status"] == "done" and not reset:
                print(f"[rhyme:{book_name}] Already done.")
                continue
            if reset:
                reset_progress(pcon, "rhyme", dynasty=book_name)

            data = await client.get(f"/rhyme/{book_name}")
            if not data:
                continue
            # API returns {Book, Categories: [{Name, Id, Tone, Chars}]}
            entries = data.get("Categories", [])
            for entry in entries:
                con.execute("""
                    INSERT INTO rhyme_entry (book, name, chars) VALUES (?, ?, ?) ON CONFLICT DO NOTHING
                """, [book_name, entry.get("Name", ""), entry.get("Chars", "")])
            upsert_progress(pcon, "rhyme", book_name, None, 0, "done", len(entries))
            print(f"[rhyme:{book_name}] {len(entries)} entries")
        print(f"[rhyme] Done: {get_row_count(con, 'rhyme_entry'):,}")
    finally:
        con.commit(); con.close()


async def _crawl_ci_tune(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        progress = get_progress(pcon, "ciTune")
        if progress and progress["status"] == "done" and not reset:
            print("[ciTune] Already done.")
            return
        data = await client.get("/ciTune")
        if not data:
            return
        tunes = data if isinstance(data, list) else data.get("CiTunes", [])
        if limit:
            tunes = tunes[:limit]
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
        upsert_progress(pcon, "ciTune", None, None, 0, "done", len(tunes))
        print(f"[ciTune] Done: {get_row_count(con, 'ci_tune'):,}")
    finally:
        con.commit(); con.close()


async def _crawl_qu_tune(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        progress = get_progress(pcon, "quTune")
        if progress and progress["status"] == "done" and not reset:
            print("[quTune] Already done.")
            return
        data = await client.get("/quTune")
        if not data:
            return
        tunes = data if isinstance(data, list) else data.get("QuTunes", [])
        if limit:
            tunes = tunes[:limit]
        for t in tunes:
            tid = t.get("Id")
            if not tid:
                continue
            content = t.get("Content", "")
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            con.execute("""
                INSERT INTO qu_tune (id, name, content) VALUES (?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
            """, [tid, t.get("Name", ""), content])
        upsert_progress(pcon, "quTune", None, None, 0, "done", len(tunes))
        print(f"[quTune] Done: {get_row_count(con, 'qu_tune'):,}")
    finally:
        con.commit(); con.close()


async def _crawl_category(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        progress = get_progress(pcon, "category")
        if progress and progress["status"] == "done" and not reset:
            print("[category] Already done.")
            return
        if reset:
            reset_progress(pcon, "category")

        data = await client.get("/category")
        if not data:
            return
        # API returns {Books: [book_name, ...]} — list of book names
        book_names = data.get("Books", [])
        if not book_names:
            # Fallback: try Categories key
            book_names = data.get("Categories", [])
        print(f"[category] Found {len(book_names)} category books")

        total = 0
        for book_name in book_names:
            if client.should_abort:
                break
            if isinstance(book_name, dict):
                book_name = book_name.get("Name", book_name.get("Title", ""))
            detail = await client.get(f"/category/{book_name}")
            if not detail or not isinstance(detail, dict):
                continue
            # detail = {Book, Categories: [{Name, Items: [{Id, Name, Alias, Note, VolumeIds}]}]}
            for cat_group in detail.get("Categories", []):
                for item in cat_group.get("Items", []):
                    cid = item.get("Id")
                    if not cid:
                        continue
                    content = json.dumps(item, ensure_ascii=False)
                    con.execute("""
                        INSERT INTO category_entry (id, book, parent_id, title, content)
                        VALUES (?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
                    """, [cid, book_name, cat_group.get("Name", ""),
                          item.get("Name", ""), content])
                    total += 1
                    if limit and total >= limit:
                        break
                if limit and total >= limit:
                    break
            if total % 500 == 0:
                print(f"[category] {total:,} entries")
                upsert_progress(pcon, "category", None, None, total, "in_progress", total)
            if limit and total >= limit:
                print(f"[category] Reached limit of {limit}")
                break
        upsert_progress(pcon, "category", None, None, 0, "done", total)
        print(f"[category] Done: {get_row_count(con, 'category_entry'):,}")
    finally:
        con.commit(); con.close()


CJK_START = 0x4E00
CJK_END = 0x9FFF


async def _crawl_char(client, reset: bool, limit: int = 0):
    con = get_db()
    pcon = con
    try:
        progress = get_progress(pcon, "char")
        if progress and progress["status"] == "done" and not reset:
            print("[char] Already done.")
            return
        if limit:
            print(f"[char] Limited to {limit} chars")
        existing = set()
        if progress and progress["status"] == "in_progress":
            rows = con.execute("SELECT char FROM char_dict").fetchall()
            existing = {r[0] for r in rows}
        print(f"[char] Crawling ({len(existing)} done)...")
        fetched = len(existing)
        for code in range(CJK_START, CJK_END + 1):
            char = chr(code)
            if char in existing:
                continue
            if client.should_abort:
                upsert_progress(pcon, "char", None, None, code, "in_progress", fetched)
                return
            data = await client.get(f"/char/{char}")
            if data:
                content = json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
                con.execute("""
                    INSERT INTO char_dict (char, content) VALUES (?, ?)
                    ON CONFLICT (char) DO UPDATE SET content = EXCLUDED.content
                """, [char, content])
                fetched += 1
            if limit and fetched >= limit:
                print(f"[char] Reached limit of {limit}")
                break
            if code % 500 == 0:
                pct = (code - CJK_START) / (CJK_END - CJK_START + 1) * 100
                print(f"[char] {fetched:,} chars ({pct:.1f}%)")
                upsert_progress(pcon, "char", None, None, code, "in_progress", fetched)
        upsert_progress(pcon, "char", None, None, 0, "done", fetched)
        print(f"[char] Done: {get_row_count(con, 'char_dict'):,}")
    finally:
        con.commit(); con.close()
