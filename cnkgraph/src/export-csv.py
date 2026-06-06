"""
Export all DuckDB tables to CSV files.
Output: data/csv/<table_name>.csv

For ci_tune and qu_tune, the JSON content column is expanded into
individual columns for a clean tabular format.

Usage:
    python src/export-csv.py
"""

import json
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from db import DATA_DIR, STAGE_TABLES

# ci_tune JSON fields -> flat CSV columns
CI_TUNE_COLUMNS = ["id", "name", "type", "aliases", "desc", "writing_count"]

# qu_tune JSON fields -> flat CSV columns
QU_TUNE_COLUMNS = ["id", "name", "path", "aliases", "name_comment", "writing_count"]


def _flatten_ci_tune(con, csv_path):
    rows = con.execute("SELECT id, name, content FROM ci_tune").fetchall()
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CI_TUNE_COLUMNS)
        for rid, name, content in rows:
            try:
                obj = json.loads(content) if content else {}
            except (json.JSONDecodeError, TypeError):
                obj = {}
            aliases = obj.get("Aliases") or []
            writer.writerow([
                rid,
                obj.get("Name") or name,
                obj.get("Type", ""),
                "|".join(str(a) for a in aliases) if aliases else "",
                obj.get("Desc", ""),
                obj.get("WritingCount", 0),
            ])
    return len(rows)


def _flatten_qu_tune(con, csv_path):
    rows = con.execute("SELECT id, name, content FROM qu_tune").fetchall()
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(QU_TUNE_COLUMNS)
        for rid, name, content in rows:
            try:
                obj = json.loads(content) if content else {}
            except (json.JSONDecodeError, TypeError):
                obj = {}
            aliases = obj.get("Aliases") or []
            writer.writerow([
                rid,
                obj.get("Name") or name,
                obj.get("Path", ""),
                "|".join(str(a) for a in aliases) if aliases else "",
                obj.get("NameComment", ""),
                obj.get("WritingCount", 0),
            ])
    return len(rows)


def export_all():
    import duckdb
    from db import get_db

    csv_dir = os.path.join(DATA_DIR, "csv")
    os.makedirs(csv_dir, exist_ok=True)

    total_files = 0
    total_rows = 0

    # Collect all tables across stages + supplement
    all_tables = []
    for stage in range(1, 6):
        all_tables.extend(STAGE_TABLES[stage])
    supp_tables = ["supplement_glossary", "supplement_book", "supplement_book_volume",
                   "supplement_category_book", "supplement_category_item", "supplement_char"]
    all_tables.extend(supp_tables)

    con = get_db()
    try:
        for table in all_tables:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count == 0:
                    print(f"  {table}: 0 rows (skipped)")
                    continue

                csv_path = os.path.join(csv_dir, f"{table}.csv")

                if table == "ci_tune":
                    count = _flatten_ci_tune(con, csv_path)
                    print(f"  {table}: {count:,} rows (flattened) -> {csv_path}")
                elif table == "qu_tune":
                    count = _flatten_qu_tune(con, csv_path)
                    print(f"  {table}: {count:,} rows (flattened) -> {csv_path}")
                else:
                    con.execute(f"COPY {table} TO '{csv_path}' (HEADER, DELIMITER ',')")
                    print(f"  {table}: {count:,} rows -> {csv_path}")

                total_files += 1
                total_rows += count
            except Exception as e:
                print(f"  {table}: ERROR - {e}")
    finally:
        con.close()

    print(f"\nExported {total_files} tables, {total_rows:,} total rows to {csv_dir}")


if __name__ == "__main__":
    export_all()
