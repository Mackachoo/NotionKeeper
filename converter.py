#!/usr/bin/env python3
"""
NotionKeeper Converter
=====================
Converts between Notion (Markdown + CSV) and LegendKeeper (JSON/Markdown) formats.

Usage:
    python converter.py notion-to-lk <notion_dir> <output_dir>
    python converter.py lk-to-notion <lk_input> <output_dir>
"""

import sys
from pathlib import Path

from src.logger import Logger
from src.notion_parser import NotionParser
from src.legendkeeper_parser import LegendKeeperParser
from src.notion_exporter import NotionExporter
from src.legendkeeper_exporter import LegendKeeperExporter


def main():
    """Main entry point for the converter."""
    logger = Logger()

    if len(sys.argv) < 4:
        logger.error("❌ Invalid arguments")
        print("\nUsage:")
        print("  python converter.py notion-to-lk <notion_dir> <output_dir>")
        print("  python converter.py lk-to-notion <lk_input> <output_dir>")
        print("\nExamples:")
        print(
            "  python converter.py notion-to-lk exports/notion/realms/ imports/legendkeeper/"
        )
        print(
            "  python converter.py lk-to-notion exports/legendkeeper/Realms.json imports/notion/"
        )
        print("\nDocumentation: See docs/QUICKREF.md for quick reference")
        sys.exit(1)

    command = sys.argv[1]
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    logger.info(f"🚀 Starting conversion: {command}")
    logger.info(f"📂 Input: {input_path}")
    logger.info(f"📂 Output: {output_path}")

    try:
        if command == "notion-to-lk":
            convert_notion_to_legendkeeper(input_path, output_path, logger)
        elif command == "lk-to-notion":
            convert_legendkeeper_to_notion(input_path, output_path, logger)
        else:
            logger.error(f"❌ Unknown command: {command}")
            sys.exit(1)

        logger.success("✅ Conversion completed successfully!")

    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        logger.exception(e)
        sys.exit(1)


def convert_notion_to_legendkeeper(input_path: Path, output_path: Path, logger: Logger):
    """Convert Notion export to LegendKeeper format."""
    logger.section("Converting Notion → LegendKeeper")

    # Parse Notion files
    logger.step("Parsing Notion files")
    parser = NotionParser(logger)
    data = parser.parse_directory(input_path)

    # Export to LegendKeeper format
    logger.step("Exporting to LegendKeeper format")
    exporter = LegendKeeperExporter(logger)
    exporter.export(data, output_path)


def convert_legendkeeper_to_notion(input_path: Path, output_path: Path, logger: Logger):
    """Convert LegendKeeper export to Notion format."""
    logger.section("Converting LegendKeeper → Notion")

    # Parse LegendKeeper files
    logger.step("Parsing LegendKeeper files")
    parser = LegendKeeperParser(logger)

    if input_path.suffix == ".json":
        data = parser.parse_json(input_path)
    else:
        data = parser.parse_directory(input_path)

    # Export to Notion format
    logger.step("Exporting to Notion format")
    exporter = NotionExporter(logger)
    exporter.export(data, output_path)


if __name__ == "__main__":
    main()
