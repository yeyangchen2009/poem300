"""
Export all DuckDB tables to CSV files.
Output: data/csv/<table_name>.csv

Usage:
    python src/export-csv.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from db import DATA_DIR, STAGE_DB

STAGE_TABLES = {
    1: ["dynasty", "era_year"],
    2: ["person", "person_alias", "person_hometown", "person_detail"],
    3: ["writing", "writing_clause", "writing_comment", "writing_link", "writing_allusion"],
    4: ["region", "region_history", "scenery"],
    5: ["book", "book_volume", "glossary", "rhyme_entry", "rhyme_char",
        "ci_tune", "qu_tune", "category_entry", "char_dict"],
}


def export_all():
    import duckdb

    csv_dir = os.path.join(DATA_DIR, "csv")
    os.makedirs(csv_dir, exist_ok=True)

    total_files = 0
    total_rows = 0

    for stage, tables in STAGE_TABLES.items():
        db_path = os.path.join(DATA_DIR, STAGE_DB[stage])
        if not os.path.exists(db_path):
            print(f"[Stage {stage}] {STAGE_DB[stage]} not found, skipping")
            continue

        con = duckdb.connect(db_path, read_only=True)
        for table in tables:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count == 0:
                    print(f"  {table}: 0 rows (skipped)")
                    continue
                csv_path = os.path.join(csv_dir, f"{table}.csv")
                con.execute(f"COPY {table} TO '{csv_path}' (HEADER, DELIMITER ',')")
                print(f"  {table}: {count:,} rows -> {csv_path}")
                total_files += 1
                total_rows += count
            except Exception as e:
                print(f"  {table}: ERROR - {e}")
        con.close()

    print(f"\nExported {total_files} tables, {total_rows:,} total rows to {csv_dir}")


if __name__ == "__main__":
    export_all()
