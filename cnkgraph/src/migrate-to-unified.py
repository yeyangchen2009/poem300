"""
One-time migration: copy data from old 7 DuckDB files → unified cnkgraph.duckdb.

Usage:
    python src/migrate-to-unified.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import duckdb
from db import get_db, DATA_DIR

OLD_DBS = {
    "calendar": "calendar.duckdb",
    "people": "people.duckdb",
    "writing": "writing.duckdb",
    "region": "region.duckdb",
    "reference": "reference.duckdb",
    "progress": "crawl_progress.duckdb",
    "supplement": "supplement.duckdb",
}

TABLE_MAP = {
    "calendar": ["dynasty", "era_year"],
    "people": ["person", "person_alias", "person_hometown", "person_detail"],
    "writing": ["writing", "writing_clause", "writing_comment", "writing_link", "writing_allusion"],
    "region": ["region", "region_history", "scenery"],
    "reference": ["book", "book_volume", "glossary", "rhyme_entry", "rhyme_char",
                   "ci_tune", "qu_tune", "category_entry", "char_dict"],
    "progress": ["crawl_progress"],
    "supplement": ["supplement_glossary", "supplement_book", "supplement_book_volume",
                    "supplement_category_book", "supplement_category_item", "supplement_char"],
}

# Tables with auto-increment IDs need special handling — skip PK conflict
SKIP_CONFLICT = {"person_alias", "person_hometown", "person_detail",
                 "writing_clause", "writing_comment", "writing_link", "writing_allusion",
                 "region_history", "scenery", "glossary", "rhyme_entry", "rhyme_char"}


def migrate():
    con = get_db()
    total_rows = 0

    for db_name, filename in OLD_DBS.items():
        db_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(db_path):
            print(f"[{db_name}] {filename} not found, skipping")
            continue

        print(f"\n=== Migrating {db_name} ===")
        old = duckdb.connect(db_path, read_only=True)

        for table in TABLE_MAP.get(db_name, []):
            try:
                count = old.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count == 0:
                    print(f"  {table}: 0 rows (skipped)")
                    continue

                cols = [r[0] for r in old.execute(f"DESCRIBE {table}").fetchall()]
                col_list = ", ".join(cols)
                placeholders = ", ".join(["?"] * len(cols))

                # Use ATTACH for cross-DB copy
                alias = f"old_{db_name}"
                try:
                    con.execute(f"DETACH IF EXISTS {alias}")
                except Exception:
                    pass
                con.execute(f"ATTACH '{db_path}' AS {alias} (READ_ONLY)")

                if table in SKIP_CONFLICT:
                    sql = f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM {alias}.{table}"
                elif table == "crawl_progress":
                    pk_cols = "module, dynasty, author_id"
                    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in ("module", "dynasty", "author_id"))
                    sql = f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM {alias}.{table} ON CONFLICT ({pk_cols}) DO UPDATE SET {updates}"
                elif table == "supplement_glossary":
                    pk_cols = "id, kind"
                    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in ("id", "kind"))
                    sql = f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM {alias}.{table} ON CONFLICT ({pk_cols}) DO UPDATE SET {updates}"
                else:
                    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in ("id", "name", "char"))
                    pk_col = cols[0]
                    if updates:
                        sql = f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM {alias}.{table} ON CONFLICT ({pk_col}) DO UPDATE SET {updates}"
                    else:
                        sql = f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM {alias}.{table} ON CONFLICT ({pk_col}) DO NOTHING"

                con.execute(sql)
                con.execute(f"DETACH {alias}")

                new_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {table}: {count:,} rows migrated (now {new_count:,})")
                total_rows += count

            except Exception as e:
                print(f"  {table}: ERROR - {e}")

        old.close()

    con.close()
    print(f"\n=== Migration complete: {total_rows:,} total rows ===")


if __name__ == "__main__":
    migrate()
