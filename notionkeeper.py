#!/usr/bin/env python3
"""CLI wrapper for the NotionKeeper conversion tool.

This script sits at the repository root and delegates to `src/notion_keeper.py`.
It modifies sys.path so the `src` package can be imported directly.
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="NotionKeeper — convert Notion exports to LegendKeeper format"
    )
    parser.add_argument(
        "--data",
        "-d",
        default="exports",
        help="Path to Notion export directory (default: exports)",
    )
    parser.add_argument(
        "--out",
        "-o",
        default="imports",
        help="Output directory for cleaned LegendKeeper data (default: imports)",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Do not write a log file; only print to console",
    )

    args = parser.parse_args()

    # Ensure repository `src` directory is importable
    repo_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    try:
        from converter import NotionKeeper
    except Exception as e:
        print(f"Failed to import NotionKeeper from src/: {e}")
        sys.exit(2)

    nk = NotionKeeper(data_path=args.data)
    if not args.no_log:
        nk.start_logging()
    try:
        nk.to_legendkeeper(export_path=args.out)
    finally:
        if not args.no_log:
            nk.stop_logging()


if __name__ == "__main__":
    main()
