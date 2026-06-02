"""
DuckDB multi-database schema: each stage gets its own .duckdb file.

Files:
  data/calendar.duckdb       — Stage 1: dynasty + era_year
  data/people.duckdb         — Stage 2: person + person_alias + person_hometown + person_detail
  data/writing.duckdb        — Stage 3: writing + writing_clause + writing_comment + writing_link + writing_allusion
  data/region.duckdb         — Stage 4: region + region_history + scenery
  data/reference.duckdb      — Stage 5: book + book_volume + glossary + rhyme_entry + rhyme_char + ci_tune + qu_tune + category_entry + char_dict
  data/crawl_progress.duckdb — All stages: crawl_progress
"""

import os
import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

STAGE_DB = {
    1: "calendar.duckdb",
    2: "people.duckdb",
    3: "writing.duckdb",
    4: "region.duckdb",
    5: "reference.duckdb",
}

PROGRESS_DB = "crawl_progress.duckdb"

# Per-stage DDL. No cross-stage REFERENCES (person.id not referenced from writing, etc.).
# Same-stage REFERENCES are fine.

DDL_CALENDAR = """
CREATE TABLE IF NOT EXISTS dynasty (
    name        TEXT PRIMARY KEY,
    begin_year  INTEGER,
    end_year    INTEGER
);
COMMENT ON TABLE dynasty IS '朝代表，来自 /api/calendar';
COMMENT ON COLUMN dynasty.name IS '朝代名，如 唐朝、宋朝';
COMMENT ON COLUMN dynasty.begin_year IS '朝代起始年份（公元纪年），如 618';
COMMENT ON COLUMN dynasty.end_year IS '朝代终止年份（公元纪年），如 907';

CREATE TABLE IF NOT EXISTS era_year (
    name        TEXT PRIMARY KEY,
    dynasty     TEXT,
    begin_year  INTEGER,
    end_year    INTEGER
);
COMMENT ON TABLE era_year IS '年号表，来自 /api/calendar/{dynasty}';
COMMENT ON COLUMN era_year.name IS '年号名，如 开元、绍兴';
COMMENT ON COLUMN era_year.dynasty IS '所属朝代';
COMMENT ON COLUMN era_year.begin_year IS '年号起始年';
COMMENT ON COLUMN era_year.end_year IS '年号终止年';
"""

DDL_PEOPLE = """
CREATE SEQUENCE IF NOT EXISTS person_alias_seq START 1;
CREATE SEQUENCE IF NOT EXISTS person_hometown_seq START 1;
CREATE SEQUENCE IF NOT EXISTS person_detail_seq START 1;

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
COMMENT ON TABLE person IS '历史人物表，来自 /api/people/{dynasty} 列表 + /api/people/{id} 详情';
COMMENT ON COLUMN person.id IS 'API 人物唯一 ID，如 李白=15188';
COMMENT ON COLUMN person.name IS '姓名';
COMMENT ON COLUMN person.surname IS '姓氏（用于按姓检索）';
COMMENT ON COLUMN person.dynasty IS '朝代细分，如 盛唐、中唐、晚唐';
COMMENT ON COLUMN person.birth_year IS '出生年份（文本，部分为 null）';
COMMENT ON COLUMN person.death_year IS '去世年份（文本，部分为 null）';

CREATE TABLE IF NOT EXISTS person_alias (
    id          INTEGER PRIMARY KEY DEFAULT nextval('person_alias_seq'),
    person_id   INTEGER NOT NULL REFERENCES person(id),
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    source      TEXT
);
COMMENT ON TABLE person_alias IS '人物别名表（字/号/谥号/行第等）';
COMMENT ON COLUMN person_alias.type IS '别名类型：Zi=字, Hao=号, ShiHao=谥号, HangDi=行第, FamousName=美称, BieCheng=别称, FengJue=封爵, SuXing=俗姓';

CREATE TABLE IF NOT EXISTS person_hometown (
    id          INTEGER PRIMARY KEY DEFAULT nextval('person_hometown_seq'),
    person_id   INTEGER NOT NULL REFERENCES person(id),
    region_id   TEXT,
    name        TEXT
);
COMMENT ON TABLE person_hometown IS '人物籍贯表，来自 Person.Hometown';
COMMENT ON COLUMN person_hometown.region_id IS '行政区划编码，关联 region.id（跨库）';

CREATE TABLE IF NOT EXISTS person_detail (
    id          INTEGER PRIMARY KEY DEFAULT nextval('person_detail_seq'),
    person_id   INTEGER NOT NULL REFERENCES person(id),
    book        TEXT,
    content     TEXT,
    is_review   BOOLEAN DEFAULT FALSE
);
COMMENT ON TABLE person_detail IS '人物传记详情表，来自 Person.Details 数组';

CREATE INDEX IF NOT EXISTS idx_person_dynasty ON person(dynasty);
CREATE INDEX IF NOT EXISTS idx_person_alias_person ON person_alias(person_id);
CREATE INDEX IF NOT EXISTS idx_person_detail_person ON person_detail(person_id);
"""

DDL_WRITING = """
CREATE SEQUENCE IF NOT EXISTS writing_clause_seq START 1;
CREATE SEQUENCE IF NOT EXISTS writing_comment_seq START 1;
CREATE SEQUENCE IF NOT EXISTS writing_link_seq START 1;
CREATE SEQUENCE IF NOT EXISTS writing_allusion_seq START 1;

CREATE TABLE IF NOT EXISTS writing (
    id                  INTEGER PRIMARY KEY,
    author_id           INTEGER NOT NULL,
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
COMMENT ON TABLE writing IS '诗文作品表，来自 /api/writing/{朝代}/{作者} 列表';
COMMENT ON COLUMN writing.author_id IS '作者ID，关联 people.duckdb.person.id（跨库）';
COMMENT ON COLUMN writing.author_name IS '作者姓名（冗余存储，避免跨库 JOIN）';
COMMENT ON COLUMN writing.author_date_raw IS '创作年份原始文本，如 727年';
COMMENT ON COLUMN writing.author_place_raw IS '创作地点原始编码，如 CN420982';
COMMENT ON COLUMN writing.writing_type IS '体裁大类：律诗/绝句/词/曲/赋/文/联/古体/乐府等';
COMMENT ON COLUMN writing.type_detail IS '体裁细分编码：WuLv=五律, QiLv=七律, WuJue=五绝, QiJue=七绝 等';

CREATE TABLE IF NOT EXISTS writing_clause (
    id          INTEGER PRIMARY KEY DEFAULT nextval('writing_clause_seq'),
    writing_id  INTEGER NOT NULL REFERENCES writing(id),
    idx         INTEGER NOT NULL,
    content     TEXT NOT NULL,
    rhyme_char  TEXT
);
COMMENT ON TABLE writing_clause IS '诗句表，来自 Writing.Clauses 数组';

CREATE TABLE IF NOT EXISTS writing_comment (
    id          INTEGER PRIMARY KEY DEFAULT nextval('writing_comment_seq'),
    writing_id  INTEGER NOT NULL REFERENCES writing(id),
    book        TEXT,
    section     TEXT,
    content     TEXT NOT NULL,
    full_path   TEXT
);
COMMENT ON TABLE writing_comment IS '历代评注表，来自 Writing.Comments 数组';

CREATE TABLE IF NOT EXISTS writing_link (
    id              INTEGER PRIMARY KEY DEFAULT nextval('writing_link_seq'),
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
COMMENT ON TABLE writing_link IS '作品编年系地标签表，来自 /api/writing/{id} 的 Links 数组';
COMMENT ON COLUMN writing_link.region_id IS '行政区划编码，关联 region.duckdb.region.id（跨库）';

CREATE TABLE IF NOT EXISTS writing_allusion (
    id              INTEGER PRIMARY KEY DEFAULT nextval('writing_allusion_seq'),
    writing_id      INTEGER NOT NULL REFERENCES writing(id),
    allusion_index  INTEGER,
    allusion_key    TEXT,
    sentence_index  INTEGER
);
COMMENT ON TABLE writing_allusion IS '作品用典表，来自 Writing.Allusions 数组';

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
"""

DDL_REGION = """
CREATE SEQUENCE IF NOT EXISTS region_history_seq START 1;
CREATE SEQUENCE IF NOT EXISTS scenery_seq START 1;

CREATE TABLE IF NOT EXISTS region (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    latitude    REAL,
    longitude   REAL,
    parent_id   TEXT,
    people_count INTEGER DEFAULT 0,
    has_child   BOOLEAN DEFAULT FALSE
);
COMMENT ON TABLE region IS '行政区划表，来自 /api/map/region/{id}';

CREATE TABLE IF NOT EXISTS region_history (
    id              INTEGER PRIMARY KEY DEFAULT nextval('region_history_seq'),
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
COMMENT ON TABLE region_history IS '地名沿革表，来自 Region.HistoryRecords 数组';

CREATE TABLE IF NOT EXISTS scenery (
    id          INTEGER PRIMARY KEY DEFAULT nextval('scenery_seq'),
    region_id   TEXT NOT NULL REFERENCES region(id),
    name        TEXT NOT NULL
);
COMMENT ON TABLE scenery IS '景观表，来自 /api/map/scenery/{regionId}';

CREATE INDEX IF NOT EXISTS idx_region_parent ON region(parent_id);
CREATE INDEX IF NOT EXISTS idx_region_history_region ON region_history(region_id);
CREATE INDEX IF NOT EXISTS idx_scenery_region ON scenery(region_id);
"""

DDL_REFERENCE = """
CREATE SEQUENCE IF NOT EXISTS glossary_seq START 1;
CREATE SEQUENCE IF NOT EXISTS rhyme_entry_seq START 1;
CREATE SEQUENCE IF NOT EXISTS rhyme_char_seq START 1;

CREATE TABLE IF NOT EXISTS book (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    category    TEXT,
    subcategory TEXT
);
COMMENT ON TABLE book IS '古籍书目表，来自 /api/book';

CREATE TABLE IF NOT EXISTS book_volume (
    id          TEXT PRIMARY KEY,
    book_id     INTEGER NOT NULL REFERENCES book(id),
    title       TEXT,
    content     TEXT
);
COMMENT ON TABLE book_volume IS '古籍卷表，来自 /api/book/volume/{code}';

CREATE TABLE IF NOT EXISTS glossary (
    id              INTEGER PRIMARY KEY DEFAULT nextval('glossary_seq'),
    glossary_type   TEXT NOT NULL,
    source_id       INTEGER,
    text            TEXT NOT NULL,
    content         TEXT,
    spells          TEXT,
    traditional     TEXT
);
COMMENT ON TABLE glossary IS '词汇典故表，来自 /api/glossary/{type}/{id}';

CREATE TABLE IF NOT EXISTS rhyme_entry (
    id          INTEGER PRIMARY KEY DEFAULT nextval('rhyme_entry_seq'),
    book        TEXT NOT NULL,
    name        TEXT NOT NULL,
    chars       TEXT
);
COMMENT ON TABLE rhyme_entry IS '韵目表，来自 /api/rhyme/{book}';

CREATE TABLE IF NOT EXISTS rhyme_char (
    id          INTEGER PRIMARY KEY DEFAULT nextval('rhyme_char_seq'),
    book        TEXT NOT NULL,
    entry_name  TEXT NOT NULL,
    char        TEXT NOT NULL,
    detail      TEXT
);
COMMENT ON TABLE rhyme_char IS '韵字表，来自 /api/rhyme/{book}/{entry}/{char}';

CREATE TABLE IF NOT EXISTS ci_tune (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    content     TEXT
);
COMMENT ON TABLE ci_tune IS '词谱表，来自 /api/ciTune';

CREATE TABLE IF NOT EXISTS qu_tune (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    content     TEXT
);
COMMENT ON TABLE qu_tune IS '曲谱表，来自 /api/quTune';

CREATE TABLE IF NOT EXISTS category_entry (
    id          TEXT PRIMARY KEY,
    book        TEXT NOT NULL,
    parent_id   TEXT,
    title       TEXT,
    content     TEXT
);
COMMENT ON TABLE category_entry IS '类书条目表，来自 /api/category';

CREATE TABLE IF NOT EXISTS char_dict (
    char        TEXT PRIMARY KEY,
    content     TEXT
);
COMMENT ON TABLE char_dict IS '汉字字典表，来自 /api/char/{char}';

CREATE INDEX IF NOT EXISTS idx_book_category ON book(category);
CREATE INDEX IF NOT EXISTS idx_book_volume_book ON book_volume(book_id);
"""

DDL_PROGRESS = """
CREATE TABLE IF NOT EXISTS crawl_progress (
    module      TEXT NOT NULL,
    dynasty     TEXT NOT NULL DEFAULT '__ALL__',
    author_id   INTEGER NOT NULL DEFAULT -1,
    page_no     INTEGER DEFAULT 0,
    status      TEXT DEFAULT 'pending',
    row_count   INTEGER DEFAULT 0,
    updated_at  TIMESTAMP,
    PRIMARY KEY (module, dynasty, author_id)
);
COMMENT ON TABLE crawl_progress IS '断点续爬进度表';
"""

STAGE_DDL = {
    1: DDL_CALENDAR,
    2: DDL_PEOPLE,
    3: DDL_WRITING,
    4: DDL_REGION,
    5: DDL_REFERENCE,
}

STAGE_TABLES = {
    1: ["dynasty", "era_year"],
    2: ["person", "person_alias", "person_hometown", "person_detail"],
    3: ["writing", "writing_clause", "writing_comment", "writing_link", "writing_allusion"],
    4: ["region", "region_history", "scenery"],
    5: ["book", "book_volume", "glossary", "rhyme_entry", "rhyme_char",
        "ci_tune", "qu_tune", "category_entry", "char_dict"],
}

STAGE_NAMES = {
    1: "calendar",
    2: "people",
    3: "writing",
    4: "region",
    5: "reference",
}


def _exec_ddl(con, ddl: str):
    """Execute multi-statement DDL string on a DuckDB connection."""
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        lines = stmt.split("\n")
        sql_lines = [l for l in lines if l.strip() and not l.strip().startswith("--")]
        if not sql_lines:
            continue
        con.execute(stmt)


def get_db(stage: int) -> "duckdb.DuckDBPyConnection":
    """Open connection to a stage's database and ensure schema exists."""
    import duckdb
    filename = STAGE_DB[stage]
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(DATA_DIR, exist_ok=True)
    con = duckdb.connect(path)
    con.execute("SET threads=4")
    _exec_ddl(con, STAGE_DDL[stage])
    return con


def get_progress_db() -> "duckdb.DuckDBPyConnection":
    """Open connection to the crawl_progress database."""
    import duckdb
    path = os.path.join(DATA_DIR, PROGRESS_DB)
    os.makedirs(DATA_DIR, exist_ok=True)
    con = duckdb.connect(path)
    _exec_ddl(con, DDL_PROGRESS)
    return con


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
    """Print crawl progress summary across all databases."""
    print("\n=== 爬取进度 ===\n")
    for stage in range(1, 6):
        name = STAGE_NAMES[stage]
        filename = STAGE_DB[stage]
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"  Stage {stage} ({name:12s}): 未开始")
            continue
        try:
            import duckdb
            con = duckdb.connect(path, read_only=True)
            parts = []
            for table in STAGE_TABLES[stage]:
                count = get_row_count(con, table)
                if count > 0:
                    parts.append(f"{table}={count:,}")
            con.close()
            if parts:
                print(f"  Stage {stage} ({name:12s}): {', '.join(parts)}")
            else:
                print(f"  Stage {stage} ({name:12s}): 空表")
        except Exception:
            print(f"  Stage {stage} ({name:12s}): 无法读取")

    print("\n--- 断点记录 ---\n")
    progress_path = os.path.join(DATA_DIR, PROGRESS_DB)
    if not os.path.exists(progress_path):
        print("  (无记录)")
    else:
        try:
            import duckdb
            pcon = duckdb.connect(progress_path, read_only=True)
            rows = pcon.execute(
                "SELECT module, dynasty, author_id, page_no, status, row_count, updated_at "
                "FROM crawl_progress ORDER BY updated_at DESC"
            ).fetchall()
            pcon.close()
            if not rows:
                print("  (无记录)")
            for r in rows:
                dynasty_str = r[1] if r[1] and r[1] != "__ALL__" else "*"
                author_str = str(r[2]) if r[2] is not None and r[2] != -1 else "*"
                print(f"  {r[0]:15s} dynasty={dynasty_str:8s} author_id={author_str:>8s} "
                      f"page={r[3]:>5d} status={r[4]:12s} rows={r[5]:>8,d}  @ {r[6]}")
        except Exception as e:
            print(f"  (读取失败: {e})")
    print()
