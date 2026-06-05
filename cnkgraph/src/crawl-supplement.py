"""
Crawl supplementary API collections (glossary, book, category, char).
These are the 5 collections previously thought to require WeChat auth.

Modules:
  dict      - 词典 (~525K entries)
  allusion  - 典故 (~11K entries)
  buddhist  - 佛典 (~37K entries)
  book      - 古籍库 (16,221 books, metadata only, skip full text)
  category  - 类书 (8 books)
  char      - 字典 (CJK characters)

Usage:
    python src/crawl-supplement.py --module dict --limit 5
    python src/crawl-supplement.py --module allusion --limit 3
    python src/crawl-supplement.py --module book --limit 5
    python src/crawl-supplement.py --module category
    python src/crawl-supplement.py --module char --limit 10
    python src/crawl-supplement.py                    # run all
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from api import CnkgraphClient
from db import get_progress_db, get_progress, upsert_progress, reset_progress

import duckdb

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "supplement.duckdb")

DDL = """
CREATE TABLE IF NOT EXISTS supplement_glossary (
    id          INTEGER NOT NULL,
    kind        INTEGER NOT NULL,
    PRIMARY KEY (id, kind),
    word        TEXT,
    original_word TEXT,
    from_source TEXT,
    spellings   TEXT,
    explains    TEXT,
    categories  TEXT,
    count_in_writings INTEGER,
    keys        TEXT,
    related_persons TEXT,
    quotes      TEXT,
    correlations TEXT,
    ref_data    TEXT,
    raw_json    TEXT
);

CREATE TABLE IF NOT EXISTS supplement_book (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    author      TEXT,
    author_ids  TEXT,
    dynasty     TEXT,
    versions    TEXT,
    raw_json    TEXT
);

CREATE TABLE IF NOT EXISTS supplement_book_volume (
    volume_id   TEXT PRIMARY KEY,
    book_id     INTEGER,
    text        TEXT,
    html        TEXT
);

CREATE TABLE IF NOT EXISTS supplement_category_book (
    name        TEXT PRIMARY KEY,
    categories  TEXT,
    raw_json    TEXT
);

CREATE TABLE IF NOT EXISTS supplement_category_item (
    id          TEXT PRIMARY KEY,
    book_name   TEXT NOT NULL,
    name        TEXT,
    alias       TEXT,
    note        TEXT,
    volume_ids  TEXT,
    content     TEXT,
    image_urls  TEXT,
    raw_json    TEXT
);

CREATE TABLE IF NOT EXISTS supplement_char (
    char            TEXT PRIMARY KEY,
    modern_dict     TEXT,
    kangxi_dict     TEXT,
    shuowen_dict    TEXT,
    raw_json        TEXT
);

CREATE INDEX IF NOT EXISTS idx_glossary_kind ON supplement_glossary(kind);
CREATE INDEX IF NOT EXISTS idx_glossary_word ON supplement_glossary(word);
CREATE INDEX IF NOT EXISTS idx_book_dynasty ON supplement_book(dynasty);
CREATE INDEX IF NOT EXISTS idx_category_item_book ON supplement_category_item(book_name);
"""


def get_supplement_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = duckdb.connect(DB_FILE)
    con.execute("SET threads=4")
    for stmt in DDL.split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)
    return con


def _json(obj):
    return json.dumps(obj, ensure_ascii=False) if obj else None


# ---------------------------------------------------------------------------
# Module: 词典 (dict)
# ---------------------------------------------------------------------------

async def crawl_dict(client, limit: int = 0, start_id: int = None, end_id: int = None):
    """Crawl 词典 entries by ID range."""
    print("\n=== 词典 ===")
    pcon = get_progress_db()
    con = get_supplement_db()
    try:
        scan_start = start_id or 1
        scan_end = end_id or 525000

        fetched = 0
        empty_streak = 0

        for eid in range(scan_start, scan_end + 1):
            if limit and fetched >= limit:
                print(f"[dict] Reached limit of {limit}")
                break
            if client.should_abort:
                upsert_progress(pcon, "supplement_dict", None, None, eid, "in_progress", fetched)
                return

            data = await client.get(f"/glossary/词典/{eid}")
            msg = data.get("Message", "") if isinstance(data, dict) else ""
            if "未找到" in msg:
                empty_streak += 1
                if empty_streak >= 100:
                    print(f"[dict] 100 consecutive misses after ID {eid}, stopping.")
                    break
                continue
            empty_streak = 0

            if isinstance(data, dict) and data.get("Word"):
                con.execute("""
                    INSERT INTO supplement_glossary
                    (id, kind, word, original_word, from_source, spellings,
                     explains, categories, raw_json)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id, kind) DO UPDATE SET
                        word = EXCLUDED.word, raw_json = EXCLUDED.raw_json
                """, [eid, data.get("Word"), data.get("OriginalWord"),
                      data.get("From"), data.get("Spellings"),
                      _json(data.get("Explains")), _json(data.get("Categories")),
                      _json(data)])
                fetched += 1

            if eid % 1000 == 0:
                print(f"[dict] ID {eid}: {fetched} entries fetched")

        upsert_progress(pcon, "supplement_dict", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_glossary WHERE kind=1").fetchone()[0]
        print(f"[dict] Done: {fetched} new, {count} total 词典 entries")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 典故 (allusion)
# ---------------------------------------------------------------------------

async def crawl_allusion(client, limit: int = 0, start_id: int = None, end_id: int = None):
    print("\n=== 典故 ===")
    pcon = get_progress_db()
    con = get_supplement_db()
    try:
        scan_start = start_id or 1
        scan_end = end_id or 12000

        fetched = 0
        empty_streak = 0

        for eid in range(scan_start, scan_end + 1):
            if limit and fetched >= limit:
                print(f"[allusion] Reached limit of {limit}")
                break
            if client.should_abort:
                upsert_progress(pcon, "supplement_allusion", None, None, eid, "in_progress", fetched)
                return

            data = await client.get(f"/glossary/典故/{eid}")
            msg = data.get("Message", "") if isinstance(data, dict) else ""
            if "未找到" in msg:
                empty_streak += 1
                if empty_streak >= 200:
                    print(f"[allusion] 200 consecutive misses after ID {eid}, stopping.")
                    break
                continue
            empty_streak = 0

            if isinstance(data, dict) and (data.get("Keys") or data.get("Explains")):
                con.execute("""
                    INSERT INTO supplement_glossary
                    (id, kind, word, count_in_writings, keys, related_persons,
                     quotes, correlations, ref_data, explains, raw_json)
                    VALUES (?, 2, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id, kind) DO UPDATE SET raw_json = EXCLUDED.raw_json
                """, [eid, data.get("CountInWritings"), _json(data.get("Keys")),
                      _json(data.get("RelatedPersons")), _json(data.get("Quotes")),
                      _json(data.get("Correlations")), _json(data.get("References")),
                      _json(data.get("Explains")), _json(data)])
                fetched += 1

            if eid % 500 == 0:
                print(f"[allusion] ID {eid}: {fetched} entries fetched")

        upsert_progress(pcon, "supplement_allusion", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_glossary WHERE kind=2").fetchone()[0]
        print(f"[allusion] Done: {fetched} new, {count} total 典故 entries")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 佛典 (buddhist)
# ---------------------------------------------------------------------------

async def crawl_buddhist(client, limit: int = 0, start_id: int = None, end_id: int = None):
    print("\n=== 佛典 ===")
    pcon = get_progress_db()
    con = get_supplement_db()
    try:
        scan_start = start_id or 1
        scan_end = end_id or 38000

        fetched = 0
        empty_streak = 0

        for eid in range(scan_start, scan_end + 1):
            if limit and fetched >= limit:
                print(f"[buddhist] Reached limit of {limit}")
                break
            if client.should_abort:
                upsert_progress(pcon, "supplement_buddhist", None, None, eid, "in_progress", fetched)
                return

            data = await client.get(f"/glossary/佛典/{eid}")
            msg = data.get("Message", "") if isinstance(data, dict) else ""
            if "未找到" in msg:
                empty_streak += 1
                if empty_streak >= 200:
                    print(f"[buddhist] 200 consecutive misses after ID {eid}, stopping.")
                    break
                continue
            empty_streak = 0

            if isinstance(data, dict) and data.get("Word"):
                con.execute("""
                    INSERT INTO supplement_glossary
                    (id, kind, word, original_word, from_source, spellings,
                     explains, categories, raw_json)
                    VALUES (?, 3, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id, kind) DO UPDATE SET raw_json = EXCLUDED.raw_json
                """, [eid, data.get("Word"), data.get("OriginalWord"),
                      data.get("From"), data.get("Spellings"),
                      _json(data.get("Explains")), _json(data.get("Categories")),
                      _json(data)])
                fetched += 1

            if eid % 500 == 0:
                print(f"[buddhist] ID {eid}: {fetched} entries fetched")

        upsert_progress(pcon, "supplement_buddhist", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_glossary WHERE kind=3").fetchone()[0]
        print(f"[buddhist] Done: {fetched} new, {count} total 佛典 entries")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 古籍库 (book) — metadata only, skip full-text volumes
# ---------------------------------------------------------------------------

async def crawl_book(client, limit: int = 0, start_id: int = None, end_id: int = None):
    print("\n=== 古籍库 ===")
    pcon = get_progress_db()
    con = get_supplement_db()
    try:
        data = await client.get("/book")
        if not data:
            print("[book] Failed to fetch book list.")
            return

        total = data.get("Total", 0)
        categories = data.get("Categories", [])
        books = []
        for cat in categories:
            cat_name = cat.get("Name", "")
            for grp in (cat.get("Groups") or []):
                grp_name = grp.get("Name", "")
                grp_books = await client.get(f"/book/{cat_name}/{grp_name}")
                if grp_books and isinstance(grp_books, dict):
                    for b in (grp_books.get("Books") or []):
                        b["_category"] = cat_name
                        b["_group"] = grp_name
                        books.append(b)

        print(f"[book] Found {len(books)} books across {len(categories)} categories (API Total: {total})")

        if limit:
            books = books[:limit]
            print(f"[book] Limited to {len(books)} books")

        fetched = 0
        for i, b in enumerate(books):
            bid = b.get("Id")
            if not bid:
                continue
            detail = await client.get(f"/book/{bid}")
            if detail:
                book_obj = detail.get("Book", {})
                con.execute("""
                    INSERT INTO supplement_book
                    (id, name, author, author_ids, dynasty, versions, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET raw_json = EXCLUDED.raw_json
                """, [bid, book_obj.get("Name", ""), book_obj.get("Author"),
                      _json(book_obj.get("AuthorIds")), book_obj.get("Dynasty"),
                      _json(book_obj.get("Versions")), _json(detail)])
                fetched += 1

            if (i + 1) % 100 == 0:
                print(f"[book] {i+1}/{len(books)} processed")

        upsert_progress(pcon, "supplement_book", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_book").fetchone()[0]
        print(f"[book] Done: {fetched} new, {count} total books")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 类书 (category)
# ---------------------------------------------------------------------------

async def crawl_category(client, limit: int = 0, start_id: int = None, end_id: int = None):
    print("\n=== 类书 ===")
    pcon = get_progress_db()
    con = get_supplement_db()
    try:
        data = await client.get("/category")
        if not data:
            print("[category] Failed to fetch category list.")
            return

        book_names = data.get("Books", [])
        print(f"[category] Found {len(book_names)} books: {', '.join(book_names)}")

        items_total = 0
        for book_name in book_names:
            print(f"[category] Fetching tree for {book_name}...")
            tree = await client.get(f"/category/{book_name}")
            if not tree:
                print(f"[category] Failed to fetch {book_name}")
                continue

            con.execute("""
                INSERT INTO supplement_category_book (name, categories, raw_json)
                VALUES (?, ?, ?)
                ON CONFLICT (name) DO UPDATE SET raw_json = EXCLUDED.raw_json
            """, [book_name, _json(tree.get("Categories")), _json(tree)])

            # Flatten items from all categories
            for cat in (tree.get("Categories") or []):
                for item in (cat.get("Items") or []):
                    item_id = item.get("Id")
                    if not item_id:
                        continue
                    # Fetch item detail if it has volumes
                    vol_ids = item.get("VolumeIds") or []
                    content = None
                    if vol_ids:
                        vol = vol_ids[0]
                        vol_id = vol.get("Id", "")
                        if vol_id:
                            detail = await client.get(f"/category/{book_name}/{item_id}/{vol_id}")
                            if detail:
                                content = _json(detail.get("Content"))

                    con.execute("""
                        INSERT INTO supplement_category_item
                        (id, book_name, name, alias, note, volume_ids, content, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
                    """, [f"{book_name}:{item_id}", book_name, item.get("Name"),
                          item.get("Alias"), item.get("Note"),
                          _json(vol_ids), content, _json(item)])
                    items_total += 1

                    if limit and items_total >= limit:
                        break
                if limit and items_total >= limit:
                    break

            print(f"[category] {book_name}: {items_total} items cumulative")
            if limit and items_total >= limit:
                break

        upsert_progress(pcon, "supplement_category", None, None, 0, "done", items_total)
        count = con.execute("SELECT COUNT(*) FROM supplement_category_item").fetchone()[0]
        print(f"[category] Done: {items_total} new, {count} total items")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 字典 (char)
# ---------------------------------------------------------------------------

CJK_START = 0x4E00
CJK_END = 0x9FFF

# Common characters for testing
TEST_CHARS = list("天地人日月山水风云雨雪春夏秋冬花草木石金山河湖海龙凤鸟马牛羊猪狗鸡")


async def crawl_char(client, limit: int = 0, start_id: int = None, end_id: int = None):
    print("\n=== 字典 ===")
    pcon = get_progress_db()
    con = get_supplement_db()
    try:
        existing = set()
        rows = con.execute("SELECT char FROM supplement_char").fetchall()
        existing = {r[0] for r in rows}

        if limit:
            chars = TEST_CHARS[:limit]
            print(f"[char] Testing with {len(chars)} chars: {''.join(chars)}")
        else:
            chars = [chr(c) for c in range(CJK_START, CJK_END + 1) if chr(c) not in existing]
            print(f"[char] Crawling {len(chars)} CJK chars ({len(existing)} already done)")

        fetched = len(existing)
        for i, char in enumerate(chars):
            if client.should_abort:
                break
            data = await client.get(f"/char/{char}")
            if data and isinstance(data, dict):
                has_data = data.get("ModernDictionary") or data.get("KangXiDictionary") or data.get("ShuoWenDictionary")
                if has_data:
                    con.execute("""
                        INSERT INTO supplement_char
                        (char, modern_dict, kangxi_dict, shuowen_dict, raw_json)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT (char) DO UPDATE SET raw_json = EXCLUDED.raw_json
                    """, [char, _json(data.get("ModernDictionary")),
                          _json(data.get("KangXiDictionary")),
                          _json(data.get("ShuoWenDictionary")), _json(data)])
                    fetched += 1

            if (i + 1) % 50 == 0:
                print(f"[char] {i+1}/{len(chars)} checked, {fetched} with data")

        upsert_progress(pcon, "supplement_char", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_char").fetchone()[0]
        print(f"[char] Done: {fetched} new, {count} total chars")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

MODULES = {
    "dict": crawl_dict,
    "allusion": crawl_allusion,
    "buddhist": crawl_buddhist,
    "book": crawl_book,
    "category": crawl_category,
    "char": crawl_char,
}


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crawl supplementary cnkgraph APIs")
    parser.add_argument("--module", "-m", type=str, default=None,
                        choices=list(MODULES.keys()),
                        help="Run a specific module only")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of records (for testing)")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="Concurrency (default 2)")
    parser.add_argument("--reset", action="store_true",
                        help="Reset progress for selected module(s)")
    parser.add_argument("--start-id", type=int, default=None,
                        help="Start ID for dict/allusion/buddhist scan")
    parser.add_argument("--end-id", type=int, default=None,
                        help="End ID for dict/allusion/buddhist scan")
    args = parser.parse_args()

    client = CnkgraphClient(concurrency=args.concurrency)

    try:
        if args.module:
            if args.reset:
                pcon = get_progress_db()
                reset_progress(pcon, f"supplement_{args.module}")
                pcon.close()
                print(f"[reset] Cleared progress for {args.module}")
            await MODULES[args.module](client, limit=args.limit,
                                      start_id=args.start_id, end_id=args.end_id)
        else:
            for name, func in MODULES.items():
                if args.reset:
                    pcon = get_progress_db()
                    reset_progress(pcon, f"supplement_{name}")
                    pcon.close()
                await func(client, limit=args.limit,
                           start_id=args.start_id, end_id=args.end_id)

        print("\n=== Done ===")
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
