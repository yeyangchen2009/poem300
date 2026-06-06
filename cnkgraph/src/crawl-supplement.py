"""
On-demand crawl: only fetch data referenced by the 11 volumes (97 poets, 50,640 poems).
Reads from existing ODS tables in the unified DB to determine what to fetch,
then queries the API precisely.

Modules:
  dict      - 词典: extract words from writing_clause → POST /api/glossary/词典
  allusion  - 典故: extract allusion_keys → POST /api/glossary/典故/find
  buddhist  - 佛典: extract Buddhist keywords from allusions → search
  book      - 古籍库: extract book names from writing_comment → POST /Api/Book/Find
  char      - 字典: extract unique CJK chars from writing_clause → GET /api/char/{char}

Strategy change: full-volume crawl (610K) → 11-volume filtered (~14,600 = 2.4%)

Usage:
    python src/crawl-supplement.py --module dict --limit 5
    python src/crawl-supplement.py --module char --limit 10
    python src/crawl-supplement.py               # run all modules
"""

import asyncio
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from api import CnkgraphClient
from db import get_db, get_progress_db, get_progress, upsert_progress, reset_progress


def _json(obj):
    return json.dumps(obj, ensure_ascii=False) if obj else None


# ---------------------------------------------------------------------------
# Helper: extract unique CJK characters from text
# ---------------------------------------------------------------------------

CJK_RANGE = re.compile(r'[一-鿿]')


def _extract_cjk_chars(text: str) -> set:
    return set(CJK_RANGE.findall(text)) if text else set()


# ---------------------------------------------------------------------------
# Module: 词典 (dict) — from writing_clause content
# ---------------------------------------------------------------------------

async def crawl_dict(client, limit: int = 0, start_id: int = None, end_id: int = None):
    """Extract unique words from writing_clause, then batch-query the API."""
    print("\n=== 词典 (按需) ===")
    con = get_db()
    pcon = get_progress_db()
    try:
        progress = get_progress(pcon, "supplement_dict")
        if progress and progress["status"] == "done":
            print("[dict] Already done, skipping.")
            return

        # Collect all unique words from writing clauses (2-char+ segments as proxy for words)
        rows = con.execute("SELECT content FROM writing_clause WHERE content IS NOT NULL").fetchall()
        word_counts = {}
        for (content,) in rows:
            # Split by punctuation/whitespace, keep 2-4 char segments as candidate words
            segments = re.findall(r'[^\s，。！？、；：“”‘’（）《》——·…\d]+', content)
            for seg in segments:
                for length in range(2, min(5, len(seg) + 1)):
                    for start in range(len(seg) - length + 1):
                        w = seg[start:start + length]
                        word_counts[w] = word_counts.get(w, 0) + 1

        # Sort by frequency, take top candidates
        candidates = sorted(word_counts.items(), key=lambda x: -x[1])
        print(f"[dict] {len(candidates)} candidate words from {len(rows)} clauses")

        if limit:
            candidates = candidates[:limit]
            print(f"[dict] Limited to {len(candidates)} words")

        fetched = 0
        for i, (word, count) in enumerate(candidates):
            if client.should_abort:
                upsert_progress(pcon, "supplement_dict", None, None, i, "in_progress", fetched)
                return

            # Try fetching by word
            data = await client.get(f"/glossary/词典/{word}")
            if data and isinstance(data, dict) and data.get("Word"):
                con.execute("""
                    INSERT INTO supplement_glossary
                    (id, kind, word, original_word, from_source, spellings,
                     explains, categories, raw_json)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id, kind) DO UPDATE SET
                        word = EXCLUDED.word, raw_json = EXCLUDED.raw_json
                """, [data.get("Id", 0), data.get("Word"), data.get("OriginalWord"),
                      data.get("From"), data.get("Spellings"),
                      _json(data.get("Explains")), _json(data.get("Categories")),
                      _json(data)])
                fetched += 1

            if (i + 1) % 100 == 0:
                print(f"[dict] {i+1}/{len(candidates)} checked, {fetched} matched")
                upsert_progress(pcon, "supplement_dict", None, None, i + 1, "in_progress", fetched)

        upsert_progress(pcon, "supplement_dict", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_glossary WHERE kind=1").fetchone()[0]
        print(f"[dict] Done: {fetched} new, {count} total 词典 entries")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 典故 (allusion) — from writing_allusion keys
# ---------------------------------------------------------------------------

async def crawl_allusion(client, limit: int = 0, start_id: int = None, end_id: int = None):
    """Extract unique allusion keys, then search API for each."""
    print("\n=== 典故 (按需) ===")
    con = get_db()
    pcon = get_progress_db()
    try:
        progress = get_progress(pcon, "supplement_allusion")
        if progress and progress["status"] == "done":
            print("[allusion] Already done, skipping.")
            return

        # Extract unique allusion keys
        rows = con.execute(
            "SELECT DISTINCT allusion_key FROM writing_allusion WHERE allusion_key IS NOT NULL"
        ).fetchall()
        keys = [r[0] for r in rows]
        print(f"[allusion] {len(keys)} unique allusion keys")

        if limit:
            keys = keys[:limit]
            print(f"[allusion] Limited to {len(keys)} keys")

        fetched = 0
        for i, key in enumerate(keys):
            if client.should_abort:
                upsert_progress(pcon, "supplement_allusion", None, None, i, "in_progress", fetched)
                return

            # Search allusion by keyword
            data = await client.post("/glossary/典故/find", body={"key": key, "charIndex": "end"})
            if data and isinstance(data, list):
                for item in data:
                    item_id = item.get("Id")
                    if not item_id:
                        continue
                    con.execute("""
                        INSERT INTO supplement_glossary
                        (id, kind, word, count_in_writings, keys, related_persons,
                         quotes, correlations, ref_data, explains, raw_json)
                        VALUES (?, 2, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT (id, kind) DO UPDATE SET raw_json = EXCLUDED.raw_json
                    """, [item_id, item.get("CountInWritings"), _json(item.get("Keys")),
                          _json(item.get("RelatedPersons")), _json(item.get("Quotes")),
                          _json(item.get("Correlations")), _json(item.get("References")),
                          _json(item.get("Explains")), _json(item)])
                    fetched += 1
            elif data and isinstance(data, dict):
                items = data.get("Glossaries", data.get("Items", []))
                for item in items:
                    item_id = item.get("Id")
                    if not item_id:
                        continue
                    # Fetch detail
                    detail = await client.get(f"/glossary/典故/{item_id}")
                    if detail:
                        con.execute("""
                            INSERT INTO supplement_glossary
                            (id, kind, word, count_in_writings, keys, related_persons,
                             quotes, correlations, ref_data, explains, raw_json)
                            VALUES (?, 2, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT (id, kind) DO UPDATE SET raw_json = EXCLUDED.raw_json
                        """, [item_id, detail.get("CountInWritings"), _json(detail.get("Keys")),
                              _json(detail.get("RelatedPersons")), _json(detail.get("Quotes")),
                              _json(detail.get("Correlations")), _json(detail.get("References")),
                              _json(detail.get("Explains")), _json(detail)])
                        fetched += 1

            if (i + 1) % 50 == 0:
                print(f"[allusion] {i+1}/{len(keys)} searched, {fetched} entries found")
                upsert_progress(pcon, "supplement_allusion", None, None, i + 1, "in_progress", fetched)

        upsert_progress(pcon, "supplement_allusion", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_glossary WHERE kind=2").fetchone()[0]
        print(f"[allusion] Done: {fetched} new, {count} total 典故 entries")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 佛典 (buddhist) — from allusions/comments with Buddhist keywords
# ---------------------------------------------------------------------------

BUDDHIST_KEYWORDS = [
    "佛", "禅", "僧", "寺", "经", "法", "菩萨", "罗汉", "菩提", "涅槃",
    "般若", "三昧", "因果", "轮回", "净土", "莲花", "沙门", "和尚", "尼姑",
    "阿弥陀", "观音", "弥勒", "释迦", "达摩", "六祖", "五祖", "袈裟",
    "衲", "钵", "偈", "梵", "檀", "塔", "舍利", "诵", "斋", "戒",
]


async def crawl_buddhist(client, limit: int = 0, start_id: int = None, end_id: int = None):
    """Extract Buddhist-related words from allusions, then search API."""
    print("\n=== 佛典 (按需) ===")
    con = get_db()
    pcon = get_progress_db()
    try:
        progress = get_progress(pcon, "supplement_buddhist")
        if progress and progress["status"] == "done":
            print("[buddhist] Already done, skipping.")
            return

        # Find allusions with Buddhist keywords
        rows = con.execute(
            "SELECT DISTINCT allusion_key FROM writing_allusion WHERE allusion_key IS NOT NULL"
        ).fetchall()
        buddhist_keys = []
        for (key,) in rows:
            if any(kw in key for kw in BUDDHIST_KEYWORDS):
                buddhist_keys.append(key)

        # Also check writing comments for Buddhist references
        comment_rows = con.execute(
            "SELECT DISTINCT content FROM writing_comment WHERE content IS NOT NULL"
        ).fetchall()
        for (content,) in comment_rows:
            for kw in BUDDHIST_KEYWORDS:
                if kw in content:
                    # Extract surrounding context as search term
                    idx = content.find(kw)
                    start = max(0, idx - 4)
                    end = min(len(content), idx + len(kw) + 4)
                    term = content[start:end].strip()
                    if term and len(term) >= 2:
                        buddhist_keys.append(term)

        buddhist_keys = list(set(buddhist_keys))
        print(f"[buddhist] {len(buddhist_keys)} Buddhist-related search terms")

        if limit:
            buddhist_keys = buddhist_keys[:limit]
            print(f"[buddhist] Limited to {len(buddhist_keys)} terms")

        fetched = 0
        for i, key in enumerate(buddhist_keys):
            if client.should_abort:
                upsert_progress(pcon, "supplement_buddhist", None, None, i, "in_progress", fetched)
                return

            # Try searching Buddhist glossary
            data = await client.post("/glossary/佛典/find", body={"key": key, "charIndex": "end"})
            results = []
            if data and isinstance(data, list):
                results = data
            elif data and isinstance(data, dict):
                results = data.get("Glossaries", data.get("Items", []))

            for item in results:
                item_id = item.get("Id")
                if not item_id:
                    continue
                # Fetch full detail
                detail = await client.get(f"/glossary/佛典/{item_id}")
                if detail and isinstance(detail, dict) and detail.get("Word"):
                    con.execute("""
                        INSERT INTO supplement_glossary
                        (id, kind, word, original_word, from_source, spellings,
                         explains, categories, raw_json)
                        VALUES (?, 3, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT (id, kind) DO UPDATE SET raw_json = EXCLUDED.raw_json
                    """, [item_id, detail.get("Word"), detail.get("OriginalWord"),
                          detail.get("From"), detail.get("Spellings"),
                          _json(detail.get("Explains")), _json(detail.get("Categories")),
                          _json(detail)])
                    fetched += 1

            if (i + 1) % 20 == 0:
                print(f"[buddhist] {i+1}/{len(buddhist_keys)} searched, {fetched} entries found")
                upsert_progress(pcon, "supplement_buddhist", None, None, i + 1, "in_progress", fetched)

        upsert_progress(pcon, "supplement_buddhist", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_glossary WHERE kind=3").fetchone()[0]
        print(f"[buddhist] Done: {fetched} new, {count} total 佛典 entries")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 古籍库 (book) — only books referenced in writing_comment
# ---------------------------------------------------------------------------

async def crawl_book(client, limit: int = 0, start_id: int = None, end_id: int = None):
    """Extract unique book names from writing_comment, then search API."""
    print("\n=== 古籍库 (按需) ===")
    con = get_db()
    pcon = get_progress_db()
    try:
        progress = get_progress(pcon, "supplement_book")
        if progress and progress["status"] == "done":
            print("[book] Already done, skipping.")
            return

        # Extract unique book names from comments
        rows = con.execute(
            "SELECT DISTINCT book FROM writing_comment WHERE book IS NOT NULL AND book != ''"
        ).fetchall()
        book_names = list(set(r[0] for r in rows))
        print(f"[book] {len(book_names)} unique book names from comments")

        if limit:
            book_names = book_names[:limit]
            print(f"[book] Limited to {len(book_names)} books")

        fetched = 0
        for i, book_name in enumerate(book_names):
            if client.should_abort:
                upsert_progress(pcon, "supplement_book", None, None, i, "in_progress", fetched)
                return

            # Search book by name
            data = await client.post("/Api/Book/Find", body={"key": book_name, "pageNo": 1},
                                     base_url="https://api.cnkgraph.com")
            results = []
            if data and isinstance(data, list):
                results = data
            elif data and isinstance(data, dict):
                results = data.get("Books", data.get("Items", []))
                if not results and data.get("Book"):
                    results = [data]

            for item in results:
                bid = item.get("Id")
                if not bid:
                    continue
                # Fetch detail
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

            if (i + 1) % 20 == 0:
                print(f"[book] {i+1}/{len(book_names)} searched, {fetched} books found")
                upsert_progress(pcon, "supplement_book", None, None, i + 1, "in_progress", fetched)

        upsert_progress(pcon, "supplement_book", None, None, 0, "done", fetched)
        count = con.execute("SELECT COUNT(*) FROM supplement_book").fetchone()[0]
        print(f"[book] Done: {fetched} new, {count} total books")
    finally:
        con.close()
        pcon.close()


# ---------------------------------------------------------------------------
# Module: 字典 (char) — unique CJK chars from writing_clause
# ---------------------------------------------------------------------------

TEST_CHARS = list("天地人日月山水风云雨雪春夏秋冬花草木石金山河湖海龙凤鸟马牛羊猪狗鸡")


async def crawl_char(client, limit: int = 0, start_id: int = None, end_id: int = None):
    """Extract unique CJK characters from writing_clause, then query API."""
    print("\n=== 字典 (按需) ===")
    con = get_db()
    pcon = get_progress_db()
    try:
        progress = get_progress(pcon, "supplement_char")
        if progress and progress["status"] == "done":
            print("[char] Already done, skipping.")
            return

        # Get existing chars
        existing = set()
        rows = con.execute("SELECT char FROM supplement_char").fetchall()
        existing = {r[0] for r in rows}

        if limit:
            chars = TEST_CHARS[:limit]
            print(f"[char] Testing with {len(chars)} chars: {''.join(chars)}")
        else:
            # Extract unique CJK chars from all writing clauses
            clause_rows = con.execute(
                "SELECT content FROM writing_clause WHERE content IS NOT NULL"
            ).fetchall()
            all_chars = set()
            for (content,) in clause_rows:
                all_chars.update(_extract_cjk_chars(content))

            chars = sorted(all_chars - existing)
            print(f"[char] {len(all_chars)} unique CJK chars in clauses, "
                  f"{len(existing)} already done, {len(chars)} to fetch")

        fetched = len(existing)
        for i, char in enumerate(chars):
            if client.should_abort:
                upsert_progress(pcon, "supplement_char", None, None, i, "in_progress", fetched)
                return

            data = await client.get(f"/char/{char}")
            if data and isinstance(data, dict):
                has_data = (data.get("ModernDictionary") or data.get("KangXiDictionary")
                            or data.get("ShuoWenDictionary"))
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
                upsert_progress(pcon, "supplement_char", None, None, i + 1, "in_progress", fetched)

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
    "char": crawl_char,
}


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="On-demand crawl: 11-volume filtered data")
    parser.add_argument("--module", "-m", type=str, default=None,
                        choices=list(MODULES.keys()),
                        help="Run a specific module only")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of records (for testing)")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="Concurrency (default 2)")
    parser.add_argument("--reset", action="store_true",
                        help="Reset progress for selected module(s)")
    args = parser.parse_args()

    client = CnkgraphClient(concurrency=args.concurrency)

    try:
        if args.module:
            if args.reset:
                pcon = get_progress_db()
                reset_progress(pcon, f"supplement_{args.module}")
                pcon.close()
                print(f"[reset] Cleared progress for {args.module}")
            await MODULES[args.module](client, limit=args.limit)
        else:
            for name, func in MODULES.items():
                if args.reset:
                    pcon = get_progress_db()
                    reset_progress(pcon, f"supplement_{name}")
                    pcon.close()
                await func(client, limit=args.limit)

        print("\n=== Done ===")
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
