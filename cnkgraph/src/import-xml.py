"""
Import cnkgraph XML full export into SQLite.

Output: data/cnkgraph-xml.db  (separate from API DuckDB to avoid ID conflicts)

Usage:
    python src/import-xml.py                # import all parts + groups
    python src/import-xml.py --parts 31     # import specific parts only
    python src/import-xml.py --groups-only  # import groups.xml only
    python src/import-xml.py --status       # show row counts
    python src/import-xml.py --reset        # delete DB and re-import
"""

import argparse
import json
import os
import sqlite3
import sys
import time

from lxml import etree

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
XML_DIR = os.path.join(DATA_DIR, "writings")
XML_DB = os.path.join(DATA_DIR, "cnkgraph-xml.db")

BATCH_SIZE = 10000

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS xml_writing (
    id                  INTEGER PRIMARY KEY,
    author_id           INTEGER NOT NULL,
    author_name         TEXT NOT NULL,
    title               TEXT NOT NULL,
    subtitle            TEXT,
    dynasty             TEXT,
    writing_type        TEXT,
    type_detail         TEXT,
    rhyme               TEXT,
    first_clause_rhyme  TEXT,
    g_seq               INTEGER,
    has_tone            INTEGER DEFAULT 0,
    preface             TEXT,
    note                TEXT,
    tune_id             INTEGER
);

CREATE TABLE IF NOT EXISTS xml_writing_clause (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    idx             INTEGER NOT NULL,
    content         TEXT NOT NULL,
    rhyme_char      TEXT,
    rhyme_word_id   TEXT,
    tone_mark       TEXT
);

CREATE TABLE IF NOT EXISTS xml_writing_source (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    content         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xml_writing_comment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    book            TEXT,
    section         TEXT,
    content         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xml_writing_allusion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    allusion_id     INTEGER,
    allusion_key    TEXT,
    sentence_index  INTEGER
);

CREATE TABLE IF NOT EXISTS xml_writing_annotation (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    clause_idx      INTEGER NOT NULL,
    note_type       TEXT,
    note_index      INTEGER,
    content         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xml_writing_classification (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    label           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xml_writing_sentence_break (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL,
    char_offset     INTEGER NOT NULL,
    char_length     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS xml_writing_group (
    group_id        INTEGER NOT NULL,
    poem_id         INTEGER NOT NULL,
    seq             INTEGER,
    PRIMARY KEY (group_id, poem_id)
);

CREATE TABLE IF NOT EXISTS xml_import_progress (
    part_index      INTEGER PRIMARY KEY,
    poem_count      INTEGER,
    status          TEXT DEFAULT 'done',
    updated_at      TEXT
);
"""

INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_xw_author ON xml_writing(author_id);
CREATE INDEX IF NOT EXISTS idx_xw_dynasty ON xml_writing(dynasty);
CREATE INDEX IF NOT EXISTS idx_xw_type ON xml_writing(type_detail);
CREATE INDEX IF NOT EXISTS idx_xwc_writing ON xml_writing_clause(writing_id);
CREATE INDEX IF NOT EXISTS idx_xws_writing ON xml_writing_source(writing_id);
CREATE INDEX IF NOT EXISTS idx_xwcm_writing ON xml_writing_comment(writing_id);
CREATE INDEX IF NOT EXISTS idx_xwa_writing ON xml_writing_allusion(writing_id);
CREATE INDEX IF NOT EXISTS idx_xwan_writing ON xml_writing_annotation(writing_id);
CREATE INDEX IF NOT EXISTS idx_xwcl_writing ON xml_writing_classification(writing_id);
CREATE INDEX IF NOT EXISTS idx_xwsb_writing ON xml_writing_sentence_break(writing_id);
CREATE INDEX IF NOT EXISTS idx_xwg_poem ON xml_writing_group(poem_id);
"""


# ---------------------------------------------------------------------------
# Parse one Poem — single-pass child iteration
# ---------------------------------------------------------------------------

def _parse_poem(elem):
    attrs = elem.attrib
    writing_id = int(attrs.get("Id", 0))
    if not writing_id:
        return None

    g_raw = attrs.get("G")
    title_c = None
    subtitle_c = None
    preface_text = None
    note_text = None
    tune_id = None
    clauses = []
    sources = []
    comments = []
    allusions = []
    annotations = []
    classifications = []
    sentence_breaks = []

    for child in elem:
        tag = child.tag
        if tag == "Title":
            title_c = child.get("C", "")
        elif tag == "SubTitle":
            subtitle_c = child.get("C")
        elif tag == "Preface":
            preface_text = child.text
        elif tag == "Note":
            note_text = child.text
        elif tag == "Jus":
            for idx, ju in enumerate(child):
                if ju.tag != "Ju":
                    continue
                clauses.append((
                    writing_id, idx,
                    ju.get("C", ""),
                    ju.get("R"),
                    ju.get("T"),
                    ju.get("B"),
                ))
                for ns in ju:
                    if ns.tag == "Ns":
                        for n in ns:
                            if n.tag == "N":
                                annotations.append((
                                    writing_id, idx,
                                    n.get("T"),
                                    int(n.get("I", "0") or "0"),
                                    (n.text or "").strip(),
                                ))
        elif tag == "Fs":
            for f in child:
                if f.tag == "F" and f.text and f.text.strip():
                    sources.append((writing_id, f.text.strip()))
        elif tag == "CMs":
            for cm in child:
                if cm.tag != "CM":
                    continue
                c_el = cm.find("C")
                comments.append((
                    writing_id,
                    cm.get("B"),
                    cm.get("S"),
                    c_el.text.strip() if c_el is not None and c_el.text else "",
                ))
        elif tag == "As":
            for a in child:
                if a.tag != "A":
                    continue
                ai_raw = a.get("AI", "")
                si_raw = a.get("SI", "")
                allusions.append((
                    writing_id,
                    int(ai_raw) if ai_raw.isdigit() else None,
                    (a.text or "").strip(),
                    int(si_raw) if si_raw.lstrip("-").isdigit() else None,
                ))
        elif tag == "CLs":
            for cl in child:
                if cl.tag == "CL" and cl.text and cl.text.strip():
                    classifications.append((writing_id, cl.text.strip()))
        elif tag == "SIs":
            for si in child:
                if si.tag != "SI":
                    continue
                int_els = si.findall("int")
                if len(int_els) >= 2:
                    t0 = int_els[0].text or "0"
                    t1 = int_els[1].text or "0"
                    if t0.isdigit() and t1.isdigit():
                        sentence_breaks.append((writing_id, int(t0), int(t1)))
        elif tag == "TuneId":
            id_el = child.find("Id")
            if id_el is not None and id_el.text and id_el.text.strip().isdigit():
                tune_id = int(id_el.text.strip())

    writing_row = (
        writing_id,
        int(attrs.get("AId", 0)),
        attrs.get("AU", ""),
        title_c or "",
        subtitle_c,
        attrs.get("D"),
        attrs.get("T"),
        attrs.get("TD"),
        attrs.get("R"),
        attrs.get("FR"),
        int(g_raw) if g_raw and g_raw.isdigit() else None,
        1 if attrs.get("TS") == "true" else 0,
        preface_text,
        note_text,
        tune_id,
    )

    return (
        writing_row,
        clauses,
        sources,
        comments,
        allusions,
        annotations,
        classifications,
        sentence_breaks,
    )


# ---------------------------------------------------------------------------
# Batch flush
# ---------------------------------------------------------------------------

def _flush(con, batch):
    writing_rows = [b[0] for b in batch]
    con.executemany("""INSERT OR REPLACE INTO xml_writing
        (id, author_id, author_name, title, subtitle, dynasty,
         writing_type, type_detail, rhyme, first_clause_rhyme,
         g_seq, has_tone, preface, note, tune_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", writing_rows)

    all_clauses = []
    all_sources = []
    all_comments = []
    all_allusions = []
    all_annotations = []
    all_classes = []
    all_sbs = []
    for b in batch:
        all_clauses.extend(b[1])
        all_sources.extend(b[2])
        all_comments.extend(b[3])
        all_allusions.extend(b[4])
        all_annotations.extend(b[5])
        all_classes.extend(b[6])
        all_sbs.extend(b[7])

    if all_clauses:
        con.executemany("INSERT INTO xml_writing_clause (writing_id,idx,content,rhyme_char,rhyme_word_id,tone_mark) VALUES (?,?,?,?,?,?)", all_clauses)
    if all_sources:
        con.executemany("INSERT INTO xml_writing_source (writing_id,content) VALUES (?,?)", all_sources)
    if all_comments:
        con.executemany("INSERT INTO xml_writing_comment (writing_id,book,section,content) VALUES (?,?,?,?)", all_comments)
    if all_allusions:
        con.executemany("INSERT INTO xml_writing_allusion (writing_id,allusion_id,allusion_key,sentence_index) VALUES (?,?,?,?)", all_allusions)
    if all_annotations:
        con.executemany("INSERT INTO xml_writing_annotation (writing_id,clause_idx,note_type,note_index,content) VALUES (?,?,?,?,?)", all_annotations)
    if all_classes:
        con.executemany("INSERT INTO xml_writing_classification (writing_id,label) VALUES (?,?)", all_classes)
    if all_sbs:
        con.executemany("INSERT INTO xml_writing_sentence_break (writing_id,char_offset,char_length) VALUES (?,?,?)", all_sbs)


# ---------------------------------------------------------------------------
# Import one part
# ---------------------------------------------------------------------------

def import_part(con, xml_path, part_index=None):
    filename = os.path.basename(xml_path)
    total = 0
    batch = []
    start = time.time()

    for event, elem in etree.iterparse(xml_path, events=("end",), tag="Poem", recover=True):
        parsed = _parse_poem(elem)
        if parsed:
            batch.append(parsed)
            total += 1

        elem.clear()

        if len(batch) >= BATCH_SIZE:
            _flush(con, batch)
            con.commit()
            batch = []
            elapsed = time.time() - start
            print(f"    {filename}: {total:,} poems ({total / elapsed:.0f}/s)")

    if batch:
        _flush(con, batch)
        con.commit()

    elapsed = time.time() - start
    if part_index is not None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        con.execute("INSERT OR REPLACE INTO xml_import_progress VALUES (?,?,?,?)",
                    [part_index, total, "done", ts])
        con.commit()

    print(f"  {filename}: {total:,} poems in {elapsed:.1f}s")
    return total


# ---------------------------------------------------------------------------
# Import groups
# ---------------------------------------------------------------------------

def import_groups(con, groups_path):
    print("\n=== Importing groups.xml ===")
    start = time.time()
    records = []
    group_id = 0
    total_ids = 0

    for event, elem in etree.iterparse(groups_path, events=("end",), tag="Group", recover=True):
        ids = [int(id_el.text.strip()) for id_el in elem.findall("Ids/Id")
               if id_el.text and id_el.text.strip().isdigit()]
        if ids:
            group_id += 1
            for seq, poem_id in enumerate(ids):
                records.append((group_id, poem_id, seq))
            total_ids += len(ids)
        elem.clear()

    con.executemany("INSERT INTO xml_writing_group (group_id,poem_id,seq) VALUES (?,?,?)", records)
    con.commit()
    elapsed = time.time() - start
    print(f"  {group_id:,} groups, {total_ids:,} IDs in {elapsed:.1f}s")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def show_status():
    if not os.path.exists(XML_DB):
        print("\n  (数据库不存在)\n")
        return
    con = sqlite3.connect(XML_DB)
    print("\n=== XML 数据库状态 ===\n")
    for t in ["xml_writing", "xml_writing_clause", "xml_writing_source",
              "xml_writing_comment", "xml_writing_allusion", "xml_writing_annotation",
              "xml_writing_classification", "xml_writing_sentence_break", "xml_writing_group"]:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:40s} {count:>12,}")
        except Exception:
            print(f"  {t:40s} (not found)")
    print("\n--- 导入进度 ---\n")
    try:
        rows = con.execute("SELECT part_index,poem_count,status,updated_at FROM xml_import_progress ORDER BY part_index").fetchall()
        for r in rows:
            print(f"  part_{r[0]:02d}: {r[1]:>8,} poems  {r[2]}  @ {r[3]}")
    except Exception:
        print("  (无记录)")
    con.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Import XML → SQLite")
    parser.add_argument("--parts", type=int, nargs="*", default=None)
    parser.add_argument("--groups-only", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.reset and os.path.exists(XML_DB):
        os.remove(XML_DB)
        print(f"Deleted {XML_DB}")

    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(XML_DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA cache_size=-64000")  # 64MB
    for stmt in DDL.split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    con.commit()

    try:
        if args.groups_only:
            import_groups(con, os.path.join(XML_DIR, "groups.xml"))
            show_status()
            return

        # Load index
        index_path = os.path.join(XML_DIR, "index.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
            parts_info = {p["partIndex"]: p["file"] for p in index["files"]}
            print(f"=== Importing {index.get('totalPoems',0):,} poems from {len(parts_info)} parts ===")
        else:
            parts_info = {i: f"part_{i:02d}.xml" for i in range(1, 32)
                          if os.path.exists(os.path.join(XML_DIR, f"part_{i:02d}.xml"))}
            print(f"=== Importing from {len(parts_info)} parts ===")

        target_parts = args.parts if args.parts else sorted(parts_info.keys())
        grand_total = 0
        overall_start = time.time()

        for part_idx in target_parts:
            fname = parts_info.get(part_idx)
            if not fname:
                continue
            xml_path = os.path.join(XML_DIR, fname)
            if not os.path.exists(xml_path):
                continue

            # Skip done
            if not args.parts:
                done = con.execute("SELECT status,poem_count FROM xml_import_progress WHERE part_index=?",
                                   [part_idx]).fetchone()
                if done and done[0] == "done":
                    print(f"  {fname}: already done ({done[1]:,}), skipping")
                    grand_total += done[1]
                    continue

            count = import_part(con, xml_path, part_idx)
            grand_total += count

        # Groups
        if not args.parts:
            groups_path = os.path.join(XML_DIR, "groups.xml")
            if os.path.exists(groups_path):
                import_groups(con, groups_path)

        # Create indexes
        print("\nCreating indexes...")
        for stmt in INDEX_DDL.split(";"):
            s = stmt.strip()
            if s:
                con.execute(s)
        con.commit()

        elapsed = time.time() - overall_start
        print(f"\n=== Done: {grand_total:,} poems in {elapsed:.1f}s ===")
    finally:
        con.close()

    show_status()


if __name__ == "__main__":
    main()
