"""
CLI entry point for cnkgraph crawler.
All stages write to the unified data/cnkgraph.duckdb.

Usage:
    python src/crawl.py --status
    python src/crawl.py --stage 1
    python src/crawl.py --stage 3 --dynasty 唐朝
    python src/crawl.py --stage 3 --dynasty 唐朝 --author-id 15188
    python src/crawl.py --author-id 15188          # 全阶段按作者爬取
    python src/crawl.py --author-id 15188 --reset   # 重爬
    python src/crawl.py --stage 5 --module book
    python src/crawl.py --stage 3 --reset
"""

import argparse
import asyncio
import sys
import os

# Fix Windows console encoding for Chinese output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

from db import show_status, DATA_DIR, STAGE_NAMES
from api import CnkgraphClient


def parse_args():
    parser = argparse.ArgumentParser(description="cnkgraph 全量数据爬虫（统一库架构）")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4, 5],
                        help="爬取阶段: 1=年历, 2=人物, 3=诗文, 4=地理, 5=参考数据")
    parser.add_argument("--dynasty", type=str, default=None,
                        help="指定朝代 (Stage 1/2/3), 如 唐朝")
    parser.add_argument("--author-id", type=int, default=None,
                        help="指定作者ID（全阶段按作者爬取）, 如 15188=李白")
    parser.add_argument("--module", type=str, default=None,
                        choices=["book", "glossary", "rhyme", "ciTune", "quTune", "category", "char"],
                        help="参考数据子模块 (Stage 5)")
    parser.add_argument("--limit", type=int, default=0,
                        help="每个实体最多爬取 N 条 (0=不限)")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="并发数 (默认 2)")
    parser.add_argument("--status", action="store_true",
                        help="查看当前爬取进度")
    parser.add_argument("--reset", action="store_true",
                        help="重置指定阶段的进度")
    return parser.parse_args()


async def _resolve_author(client, author_id: int) -> dict | None:
    """Call API to discover author's name and dynasty."""
    data = await client.get(f"/people/{author_id}")
    if not data:
        print(f"[resolve] Failed to fetch person {author_id}")
        return None

    person_obj = data.get("Person", {})
    profile = person_obj.get("Profile", {})
    name = profile.get("Name", "")
    dynasty = profile.get("Dynasty", "")

    if not name:
        print(f"[resolve] Person {author_id} has no name in profile")
        return None

    print(f"[resolve] Author {author_id}: {name} ({dynasty})")
    return {"name": name, "dynasty": dynasty}


async def run_stage(stage: int, client, args):
    if stage == 1:
        from stages.stage1_calendar import run
        await run(client, limit=args.limit, dynasty=args.dynasty, author_id=args.author_id,
                  reset=args.reset)
    elif stage == 2:
        from stages.stage2_people import run
        await run(client, dynasty=args.dynasty, reset=args.reset, limit=args.limit,
                  author_id=args.author_id)
    elif stage == 3:
        from stages.stage3_writing import run
        await run(client, dynasty=args.dynasty, author_id=args.author_id,
                  reset=args.reset, limit=args.limit)
    elif stage == 4:
        from stages.stage4_region import run
        await run(client, reset=args.reset, limit=args.limit, author_id=args.author_id)
    elif stage == 5:
        from stages.stage5_reference import run
        await run(client, module=args.module, reset=args.reset, limit=args.limit,
                  author_id=args.author_id)


async def main():
    args = parse_args()

    if args.status:
        show_status()
        return

    print(f"Data dir: {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)

    client = CnkgraphClient(concurrency=args.concurrency)

    try:
        # Resolve author info: API first, DB fallback
        if args.author_id:
            info = await _resolve_author(client, args.author_id)
            if info:
                args.dynasty = info["dynasty"]
                print(f"[resolve] Auto-detected dynasty: {args.dynasty}")
            else:
                # Fallback: look up dynasty from person/writing table
                from db import get_db as _get_db
                _con = _get_db()
                try:
                    row = _con.execute("SELECT dynasty FROM person WHERE id = ?", [args.author_id]).fetchone()
                    if not row:
                        row = _con.execute("SELECT dynasty FROM writing WHERE author_id = ? LIMIT 1", [args.author_id]).fetchone()
                finally:
                    _con.commit()
                    _con.close()
                if row and row[0]:
                    args.dynasty = row[0]
                    print(f"[resolve] DB fallback dynasty: {args.dynasty}")
                elif not args.dynasty:
                    print(f"[resolve] Cannot determine dynasty for author {args.author_id}. "
                          f"Use --dynasty to specify.")
                    return

        if args.stage:
            print(f"\n>>> Stage {args.stage} ({STAGE_NAMES[args.stage]})")
            if args.dynasty:
                print(f"    Dynasty: {args.dynasty}")
            if args.author_id:
                print(f"    Author ID: {args.author_id}")
            if args.module:
                print(f"    Module: {args.module}")
            if args.reset:
                print(f"    Mode: RESET")
            if args.limit:
                print(f"    Limit: {args.limit} per entity")
            print()
            await run_stage(args.stage, client, args)
        else:
            stages_to_run = [1, 2, 3, 4, 5]
            for stage in stages_to_run:
                print(f"\n{'='*60}")
                print(f">>> Stage {stage} ({STAGE_NAMES[stage]})")
                print(f"{'='*60}\n")
                await run_stage(stage, client, args)

        print("\n=== Done ===\n")
        show_status()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Progress saved. Re-run to continue.")
        show_status()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
