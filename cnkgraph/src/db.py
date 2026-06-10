"""
Unified SQLite schema: single database file for all stages + supplement.

File:
  data/cnkgraph.sqlite — all tables in one database (PRD 要求 SQLite)

Tables (39):
  Stage 1 — Calendar:   dynasty, king, era_year, ganzhi_year, date_parse, date_link
  Stage 2 — People:     person, person_alias, person_hometown, person_detail,
                         biography_activity, mentionship, mentionship_writing
  Stage 3 — Writing:    writing, writing_clause, writing_comment, writing_link,
                         writing_allusion, writing_source, writing_tone
  Stage 4 — Region:     region, region_history, scenery
  Stage 5 — Reference:  book, book_volume, glossary, rhyme_entry, rhyme_char,
                         ci_tune, qu_tune, category_entry, char_dict
  Supplement:           supplement_glossary, supplement_book, supplement_book_volume,
                         supplement_category_book, supplement_category_item, supplement_char
  Progress:             crawl_progress
"""

import os
import datetime
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "cnkgraph.sqlite")

# ---------------------------------------------------------------------------
# Unified DDL — all tables in one SQLite database
# ---------------------------------------------------------------------------

DDL = """
-- ===== Stage 1: Calendar =====

CREATE TABLE IF NOT EXISTS dynasty (
    name        TEXT PRIMARY KEY,
    begin_year  INTEGER,
    end_year    INTEGER
);

CREATE TABLE IF NOT EXISTS era_year (
    name        TEXT PRIMARY KEY,
    dynasty     TEXT,
    begin_year  INTEGER,
    end_year    INTEGER
);

CREATE TABLE IF NOT EXISTS king (
    id              INTEGER PRIMARY KEY,
    name            TEXT,
    dynasty         TEXT NOT NULL,
    govern_begin    TEXT,
    govern_end      TEXT,
    author_id       INTEGER
);

CREATE TABLE IF NOT EXISTS ganzhi_year (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ganzhi      TEXT NOT NULL,
    year        INTEGER NOT NULL,
    link_count  INTEGER DEFAULT 0,
    UNIQUE(ganzhi, year)
);

CREATE TABLE IF NOT EXISTS date_parse (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    input_key   TEXT NOT NULL UNIQUE,
    year        TEXT,
    year_ganzhi TEXT,
    month       TEXT,
    day         TEXT,
    day_ganzhi  TEXT,
    era_name    TEXT,
    era_id      INTEGER,
    link_count  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS date_link (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    input_key       TEXT NOT NULL,
    label_type      INTEGER,
    label_identity  TEXT,
    resource_type   INTEGER,
    resource_id     INTEGER,
    value           TEXT,
    start           INTEGER,
    length          INTEGER,
    weight          INTEGER DEFAULT 0
);

-- ===== Stage 2: People =====

CREATE TABLE IF NOT EXISTS person (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    surname     TEXT,
    dynasty     TEXT,
    birth_year  TEXT,
    death_year  TEXT,
    birth_day   TEXT,
    death_day   TEXT
);

CREATE TABLE IF NOT EXISTS person_alias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id   INTEGER NOT NULL REFERENCES person(id),
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    source      TEXT
);

CREATE TABLE IF NOT EXISTS person_hometown (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id   INTEGER NOT NULL REFERENCES person(id),
    region_id   TEXT,
    name        TEXT
);

CREATE TABLE IF NOT EXISTS person_detail (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id   INTEGER NOT NULL REFERENCES person(id),
    book        TEXT,
    content     TEXT,
    is_review   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS biography_activity (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL REFERENCES person(id),
    year            INTEGER,
    date_text       TEXT,
    place_region_id TEXT,
    place_detail    TEXT,
    title           TEXT,
    activity        TEXT,
    related_people  TEXT,
    from_book       TEXT,
    raw_json        TEXT
);

CREATE TABLE IF NOT EXISTS mentionship (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL,
    target_id       INTEGER NOT NULL,
    target_name     TEXT,
    direction       TEXT,
    UNIQUE(person_id, target_id, direction)
);

CREATE TABLE IF NOT EXISTS mentionship_writing (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL,
    target_id       INTEGER NOT NULL,
    writing_id      INTEGER
);

-- ===== Stage 3: Writing =====

CREATE TABLE IF NOT EXISTS writing (
    id                  INTEGER PRIMARY KEY,
    author_id           INTEGER NOT NULL REFERENCES person(id),
    author_name         TEXT NOT NULL,
    title               TEXT NOT NULL,
    dynasty             TEXT,
    author_date_raw     TEXT,
    author_place_raw    TEXT,
    writing_type        TEXT,
    type_detail         TEXT,
    rhyme               TEXT,
    first_clause_rhyme  TEXT,
    rank                INTEGER DEFAULT 0,
    preface             TEXT,
    note                TEXT
);

CREATE TABLE IF NOT EXISTS writing_clause (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id  INTEGER NOT NULL REFERENCES writing(id),
    idx         INTEGER NOT NULL,
    content     TEXT NOT NULL,
    rhyme_char  TEXT
);

CREATE TABLE IF NOT EXISTS writing_comment (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id  INTEGER NOT NULL REFERENCES writing(id),
    book        TEXT,
    section     TEXT,
    content     TEXT NOT NULL,
    full_path   TEXT
);

CREATE TABLE IF NOT EXISTS writing_link (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL REFERENCES writing(id),
    label_type      TEXT NOT NULL,
    label_identity  TEXT,
    value           TEXT NOT NULL,
    resource_path   TEXT,
    year            TEXT,
    month           TEXT,
    region_id       TEXT,
    confident_level INTEGER DEFAULT 0,
    weight          INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS writing_allusion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id      INTEGER NOT NULL REFERENCES writing(id),
    allusion_index  INTEGER,
    allusion_key    TEXT,
    sentence_index  INTEGER
);

CREATE TABLE IF NOT EXISTS writing_source (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id  INTEGER NOT NULL REFERENCES writing(id),
    content     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS writing_tone (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    writing_id  INTEGER NOT NULL REFERENCES writing(id),
    clause_idx  INTEGER NOT NULL,
    char_idx    INTEGER NOT NULL,
    char        TEXT,
    tone        TEXT
);

-- ===== Stage 4: Region =====

CREATE TABLE IF NOT EXISTS region (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    latitude    REAL,
    longitude   REAL,
    parent_id   TEXT,
    people_count INTEGER DEFAULT 0,
    has_child   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS region_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id       TEXT NOT NULL REFERENCES region(id),
    history_id      TEXT,
    name            TEXT NOT NULL,
    new_name        TEXT,
    type            TEXT,
    begin_year      INTEGER,
    end_year        INTEGER,
    begin_reason    TEXT,
    end_reason      TEXT,
    belong_to       TEXT,
    external_id     TEXT,
    latitude        REAL,
    longitude       REAL
);

CREATE TABLE IF NOT EXISTS scenery (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id   TEXT NOT NULL REFERENCES region(id),
    name        TEXT NOT NULL
);

-- ===== Stage 5: Reference =====

CREATE TABLE IF NOT EXISTS book (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    category    TEXT,
    subcategory TEXT
);

CREATE TABLE IF NOT EXISTS book_volume (
    id          TEXT PRIMARY KEY,
    book_id     INTEGER NOT NULL REFERENCES book(id),
    title       TEXT,
    content     TEXT
);

CREATE TABLE IF NOT EXISTS glossary (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    glossary_type   TEXT NOT NULL,
    source_id       INTEGER,
    text            TEXT NOT NULL,
    content         TEXT,
    spells          TEXT,
    traditional     TEXT
);

CREATE TABLE IF NOT EXISTS rhyme_entry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    book        TEXT NOT NULL,
    name        TEXT NOT NULL,
    chars       TEXT
);

CREATE TABLE IF NOT EXISTS rhyme_char (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    book        TEXT NOT NULL,
    entry_name  TEXT NOT NULL,
    char        TEXT NOT NULL,
    detail      TEXT
);

CREATE TABLE IF NOT EXISTS ci_tune (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    content     TEXT
);

CREATE TABLE IF NOT EXISTS qu_tune (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    content     TEXT
);

CREATE TABLE IF NOT EXISTS category_entry (
    id          TEXT PRIMARY KEY,
    book        TEXT NOT NULL,
    parent_id   TEXT,
    title       TEXT,
    content     TEXT
);

CREATE TABLE IF NOT EXISTS char_dict (
    char        TEXT PRIMARY KEY,
    content     TEXT
);

-- ===== Supplement (on-demand crawl) =====

CREATE TABLE IF NOT EXISTS supplement_glossary (
    id              INTEGER NOT NULL,
    kind            INTEGER NOT NULL,
    word            TEXT,
    original_word   TEXT,
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
    raw_json    TEXT,
    PRIMARY KEY (id, kind)
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

-- ===== Progress =====

CREATE TABLE IF NOT EXISTS crawl_progress (
    module      TEXT NOT NULL,
    dynasty     TEXT NOT NULL DEFAULT '__ALL__',
    author_id   INTEGER NOT NULL DEFAULT -1,
    page_no     INTEGER DEFAULT 0,
    status      TEXT DEFAULT 'pending',
    row_count   INTEGER DEFAULT 0,
    updated_at  TEXT,
    PRIMARY KEY (module, dynasty, author_id)
);

-- ===== Indexes =====

CREATE INDEX IF NOT EXISTS idx_king_dynasty ON king(dynasty);
CREATE INDEX IF NOT EXISTS idx_ganzhi_year_ganzhi ON ganzhi_year(ganzhi);
CREATE INDEX IF NOT EXISTS idx_date_parse_key ON date_parse(input_key);
CREATE INDEX IF NOT EXISTS idx_date_link_key ON date_link(input_key);

CREATE INDEX IF NOT EXISTS idx_person_dynasty ON person(dynasty);
CREATE INDEX IF NOT EXISTS idx_person_alias_person ON person_alias(person_id);
CREATE INDEX IF NOT EXISTS idx_person_detail_person ON person_detail(person_id);
CREATE INDEX IF NOT EXISTS idx_biography_person ON biography_activity(person_id);
CREATE INDEX IF NOT EXISTS idx_mentionship_person ON mentionship(person_id);
CREATE INDEX IF NOT EXISTS idx_mentionship_writing ON mentionship_writing(person_id);

CREATE INDEX IF NOT EXISTS idx_writing_author ON writing(author_id);
CREATE INDEX IF NOT EXISTS idx_writing_dynasty ON writing(dynasty);
CREATE INDEX IF NOT EXISTS idx_writing_type ON writing(writing_type);
CREATE INDEX IF NOT EXISTS idx_writing_title ON writing(title);
CREATE INDEX IF NOT EXISTS idx_writing_clause_writing ON writing_clause(writing_id);
CREATE INDEX IF NOT EXISTS idx_writing_comment_writing ON writing_comment(writing_id);
CREATE INDEX IF NOT EXISTS idx_writing_link_writing ON writing_link(writing_id);
CREATE INDEX IF NOT EXISTS idx_writing_link_type ON writing_link(label_type);
CREATE INDEX IF NOT EXISTS idx_writing_link_region ON writing_link(region_id);
CREATE INDEX IF NOT EXISTS idx_writing_allusion_writing ON writing_allusion(writing_id);
CREATE INDEX IF NOT EXISTS idx_writing_source_writing ON writing_source(writing_id);
CREATE INDEX IF NOT EXISTS idx_writing_tone_writing ON writing_tone(writing_id);

CREATE INDEX IF NOT EXISTS idx_region_parent ON region(parent_id);
CREATE INDEX IF NOT EXISTS idx_region_history_region ON region_history(region_id);
CREATE INDEX IF NOT EXISTS idx_scenery_region ON scenery(region_id);

CREATE INDEX IF NOT EXISTS idx_book_category ON book(category);
CREATE INDEX IF NOT EXISTS idx_book_volume_book ON book_volume(book_id);

CREATE INDEX IF NOT EXISTS idx_glossary_kind ON supplement_glossary(kind);
CREATE INDEX IF NOT EXISTS idx_glossary_word ON supplement_glossary(word);
CREATE INDEX IF NOT EXISTS idx_book_dynasty ON supplement_book(dynasty);
CREATE INDEX IF NOT EXISTS idx_category_item_book ON supplement_category_item(book_name);
"""

# Backward compatibility
STAGE_NAMES = {
    1: "calendar",
    2: "people",
    3: "writing",
    4: "region",
    5: "reference",
}

STAGE_TABLES = {
    1: ["dynasty", "king", "era_year", "ganzhi_year", "date_parse", "date_link"],
    2: ["person", "person_alias", "person_hometown", "person_detail",
        "biography_activity", "mentionship", "mentionship_writing"],
    3: ["writing", "writing_clause", "writing_comment", "writing_link",
        "writing_allusion", "writing_source", "writing_tone"],
    4: ["region", "region_history", "scenery"],
    5: ["book", "book_volume", "glossary", "rhyme_entry", "rhyme_char",
        "ci_tune", "qu_tune", "category_entry", "char_dict"],
}


def _exec_ddl(con, ddl: str):
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        lines = stmt.split("\n")
        sql_lines = [l for l in lines if l.strip() and not l.strip().startswith("--")]
        if not sql_lines:
            continue
        con.execute(stmt)


def get_db(stage: int = None):
    """Open connection to the unified SQLite database and ensure schema exists."""
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_FILE, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    _exec_ddl(con, DDL)
    return con


def get_progress_db():
    """Return the same connection — SQLite doesn't support concurrent writers.

    Caller should NOT close this; the data connection owner handles closing.
    If caller needs its own connection, call get_db() instead.
    """
    return get_db()


def get_row_count(con, table: str) -> int:
    result = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return result[0] if result else 0


# Sentinel values for crawl_progress PK
_DYNASTY_NONE = "__ALL__"
_AUTHOR_NONE = -1


def _pk_dynasty(dynasty: str | None) -> str:
    return dynasty if dynasty else _DYNASTY_NONE


def _pk_author(author_id: int | None) -> int:
    return author_id if author_id is not None else _AUTHOR_NONE


def get_progress(pcon, module: str, dynasty: str | None = None, author_id: int | None = None) -> dict | None:
    d = _pk_dynasty(dynasty)
    a = _pk_author(author_id)
    result = pcon.execute(
        "SELECT module, dynasty, author_id, page_no, status, row_count, updated_at "
        "FROM crawl_progress WHERE module = ? AND dynasty = ? AND author_id = ?",
        [module, d, a]
    ).fetchone()
    if result:
        return {
            "module": result[0], "dynasty": result[1], "author_id": result[2],
            "page_no": result[3], "status": result[4], "row_count": result[5],
            "updated_at": result[6]
        }
    return None


def upsert_progress(pcon, module: str, dynasty: str | None, author_id: int | None,
                    page_no: int, status: str, row_count: int):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    d = _pk_dynasty(dynasty)
    a = _pk_author(author_id)
    pcon.execute("""
        INSERT INTO crawl_progress (module, dynasty, author_id, page_no, status, row_count, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (module, dynasty, author_id) DO UPDATE SET
            page_no = EXCLUDED.page_no,
            status = EXCLUDED.status,
            row_count = EXCLUDED.row_count,
            updated_at = EXCLUDED.updated_at
    """, [module, d, a, page_no, status, row_count, now])


def reset_progress(pcon, module: str, dynasty: str | None = None):
    if dynasty:
        pcon.execute("DELETE FROM crawl_progress WHERE module = ? AND dynasty = ?", [module, dynasty])
    else:
        pcon.execute("DELETE FROM crawl_progress WHERE module = ?", [module])


def show_status():
    """Print crawl progress summary from the unified database."""
    print("\n=== 爬取进度 ===\n")

    path = DB_FILE
    if not os.path.exists(path):
        print("  (数据库不存在)")
        return

    try:
        con = sqlite3.connect(path)
        con.execute("PRAGMA foreign_keys=ON")
        for stage in range(1, 6):
            name = STAGE_NAMES[stage]
            parts = []
            for table in STAGE_TABLES[stage]:
                try:
                    count = get_row_count(con, table)
                    if count > 0:
                        parts.append(f"{table}={count:,}")
                except Exception:
                    pass
            if parts:
                print(f"  Stage {stage} ({name:12s}): {', '.join(parts)}")
            else:
                print(f"  Stage {stage} ({name:12s}): 空表")

        # Supplement tables
        supp_tables = ["supplement_glossary", "supplement_book", "supplement_book_volume",
                       "supplement_category_book", "supplement_category_item", "supplement_char"]
        parts = []
        for table in supp_tables:
            try:
                count = get_row_count(con, table)
                if count > 0:
                    parts.append(f"{table}={count:,}")
            except Exception:
                pass
        if parts:
            print(f"  {'Supplement':17s}: {', '.join(parts)}")

        # Progress records
        print("\n--- 断点记录 ---\n")
        rows = con.execute(
            "SELECT module, dynasty, author_id, page_no, status, row_count, updated_at "
            "FROM crawl_progress ORDER BY updated_at DESC"
        ).fetchall()
        if not rows:
            print("  (无记录)")
        for r in rows:
            dynasty_str = r[1] if r[1] and r[1] != "__ALL__" else "*"
            author_str = str(r[2]) if r[2] is not None and r[2] != -1 else "*"
            print(f"  {r[0]:15s} dynasty={dynasty_str:8s} author_id={author_str:>8s} "
                  f"page={r[3]:>5d} status={r[4]:12s} rows={r[5]:>8,d}  @ {r[6]}")
        con.close()
    except Exception as e:
        print(f"  (读取失败: {e})")
    print()
