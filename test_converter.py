#!/usr/bin/env python3
"""
NotionKeeper Converter Testing Program
======================================
Tests conversion chains and analyzes differences.

Usage:
    python3 test_converter.py <source> <conversion_chain>

Examples:
    # Test round-trip: Notion → LK JSON → Notion
    python3 test_converter.py testing/notion-realms notion->lk-json->notion

    # Test round-trip: LK JSON → Notion → LK JSON
    python3 test_converter.py testing/Realms.json lk-json->notion->lk-json

    # Test round-trip: LK MD → Notion → LK MD
    python3 test_converter.py testing/legendkeeper-realms lk-md->notion->lk-md
"""

import sys
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import datetime
import difflib
import json

from src.logger import Logger
from src.notion_parser import NotionParser
from src.legendkeeper_parser import LegendKeeperParser
from src.notion_exporter import NotionExporter
from src.legendkeeper_exporter import LegendKeeperExporter


class ConversionTester:
    """Tests conversion chains and analyzes results."""

    def __init__(self, logger: Logger):
        """Initialize tester with logger."""
        self.logger = logger
        self.temp_dirs = []

    def run_test(self, source_path: Path, conversion_chain: str) -> Dict[str, Any]:
        """
        Run a conversion chain test.

        Args:
            source_path: Path to source file/directory
            conversion_chain: Chain like "notion->lk-json->notion"

        Returns:
            Dict with test results
        """
        self.logger.section(f"Testing Conversion Chain: {conversion_chain}")
        self.logger.info(f"📁 Source: {source_path}")

        # Parse conversion chain
        steps = self._parse_chain(conversion_chain)
        self.logger.info(f"🔗 Chain steps: {' → '.join(steps)}")

        # Validate chain
        if not self._validate_chain(steps):
            raise ValueError(f"Invalid conversion chain: {conversion_chain}")

        # Detect source format
        source_format = self._detect_format(source_path)
        self.logger.info(f"📄 Detected source format: {source_format}")

        # Validate chain starts and ends with same format
        if steps[0] != source_format or steps[-1] != source_format:
            raise ValueError(
                f"Chain must start and end with same format. "
                f"Source is '{source_format}' but chain is '{conversion_chain}'"
            )

        # Run conversion chain
        current_path = source_path
        current_format = source_format

        conversion_results = []

        for i in range(len(steps) - 1):
            from_format = steps[i]
            to_format = steps[i + 1]

            self.logger.step(f"Step {i + 1}: {from_format} → {to_format}")

            # Create temp directory for output
            temp_dir = Path(tempfile.mkdtemp(prefix=f"notionkeeper_test_{i}_"))
            self.temp_dirs.append(temp_dir)

            # Run conversion
            output_path = self._run_conversion(
                current_path, from_format, to_format, temp_dir
            )

            conversion_results.append(
                {
                    "step": i + 1,
                    "from": from_format,
                    "to": to_format,
                    "input": str(current_path),
                    "output": str(output_path),
                }
            )

            current_path = output_path
            current_format = to_format

        # Compare source with final output
        self.logger.step("Analyzing differences")
        differences = self._compare_outputs(source_path, current_path, source_format)

        # Generate report
        report = {
            "source": str(source_path),
            "source_format": source_format,
            "chain": conversion_chain,
            "steps": conversion_results,
            "differences": differences,
            "timestamp": datetime.now().isoformat(),
        }

        return report

    def _parse_chain(self, chain: str) -> List[str]:
        """Parse conversion chain string into steps."""
        return chain.split("->")

    def _validate_chain(self, steps: List[str]) -> bool:
        """Validate that chain steps are valid formats."""
        valid_formats = {"notion", "lk-json", "lk-md"}
        return all(step in valid_formats for step in steps)

    def _detect_format(self, path: Path) -> str:
        """Detect format of source."""
        if not path.exists():
            raise ValueError(f"Source does not exist: {path}")

        if path.is_file():
            if path.suffix == ".json":
                return "lk-json"
            else:
                raise ValueError(f"Unknown file format: {path}")

        # Directory - check contents
        if list(path.glob("*.md")):
            # Check if it's Notion (has IDs in filenames) or LK (no IDs)
            md_files = list(path.glob("*.md"))
            if md_files:
                # Notion files have 32-char hex IDs
                import re

                if re.search(r"[a-f0-9]{32}", md_files[0].stem):
                    return "notion"
                else:
                    return "lk-md"

        raise ValueError(f"Could not detect format of: {path}")

    def _run_conversion(
        self, input_path: Path, from_format: str, to_format: str, output_dir: Path
    ) -> Path:
        """Run a single conversion step."""
        if from_format == "notion" and to_format == "lk-json":
            return self._notion_to_lk(input_path, output_dir)
        elif from_format == "notion" and to_format == "lk-md":
            return self._notion_to_lk(input_path, output_dir)
        elif from_format == "lk-json" and to_format == "notion":
            return self._lk_to_notion(input_path, output_dir, is_json=True)
        elif from_format == "lk-md" and to_format == "notion":
            return self._lk_to_notion(input_path, output_dir, is_json=False)
        elif from_format == "lk-json" and to_format == "lk-md":
            # Convert through notion as intermediate
            temp_notion = Path(tempfile.mkdtemp(prefix="notion_temp_"))
            self.temp_dirs.append(temp_notion)
            notion_path = self._lk_to_notion(input_path, temp_notion, is_json=True)
            return self._notion_to_lk(notion_path, output_dir)
        elif from_format == "lk-md" and to_format == "lk-json":
            # Convert through notion as intermediate
            temp_notion = Path(tempfile.mkdtemp(prefix="notion_temp_"))
            self.temp_dirs.append(temp_notion)
            notion_path = self._lk_to_notion(input_path, temp_notion, is_json=False)
            return self._notion_to_lk(notion_path, output_dir)
        else:
            raise ValueError(f"Unsupported conversion: {from_format} -> {to_format}")

    def _notion_to_lk(self, input_path: Path, output_dir: Path) -> Path:
        """Convert Notion to LegendKeeper."""
        parser = NotionParser(self.logger)
        data = parser.parse_directory(input_path)

        exporter = LegendKeeperExporter(self.logger)
        exporter.export(data, output_dir)

        # Return the main output (JSON file or directory)
        json_files = list(output_dir.glob("*.json"))
        if json_files:
            return json_files[0]

        # Or return the markdown directory
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        if subdirs:
            return subdirs[0]

        return output_dir

    def _lk_to_notion(self, input_path: Path, output_dir: Path, is_json: bool) -> Path:
        """Convert LegendKeeper to Notion."""
        parser = LegendKeeperParser(self.logger)

        if is_json:
            data = parser.parse_json(input_path)
        else:
            data = parser.parse_directory(input_path)

        exporter = NotionExporter(self.logger)
        exporter.export(data, output_dir)

        return output_dir

    def _compare_outputs(
        self, source_path: Path, output_path: Path, format_type: str
    ) -> Dict[str, Any]:
        """Compare source and output to find differences."""
        differences = {
            "format": format_type,
            "file_differences": [],
            "content_differences": [],
            "structure_differences": [],
            "summary": {},
        }

        if format_type == "notion":
            self._compare_notion_dirs(source_path, output_path, differences)
        elif format_type == "lk-json":
            self._compare_json_files(source_path, output_path, differences)
        elif format_type == "lk-md":
            self._compare_lk_md_dirs(source_path, output_path, differences)

        # Generate summary
        differences["summary"] = {
            "total_file_diffs": len(differences["file_differences"]),
            "total_content_diffs": len(differences["content_differences"]),
            "total_structure_diffs": len(differences["structure_differences"]),
        }

        return differences

    def _compare_notion_dirs(self, source: Path, output: Path, differences: Dict):
        """Compare two Notion directories."""
        source_files = self._get_file_list(source, relative_to=source)
        output_files = self._get_file_list(output, relative_to=output)

        # Find missing/extra files
        source_set = set(source_files)
        output_set = set(output_files)

        missing = source_set - output_set
        extra = output_set - source_set

        if missing:
            differences["file_differences"].append(
                {"type": "missing_files", "files": sorted(list(missing))}
            )

        if extra:
            differences["file_differences"].append(
                {"type": "extra_files", "files": sorted(list(extra))}
            )

        # Compare common files
        common = source_set & output_set
        for rel_path in sorted(common):
            source_file = source / rel_path
            output_file = output / rel_path

            if source_file.suffix == ".md":
                self._compare_text_files(source_file, output_file, differences)

    def _compare_json_files(self, source: Path, output: Path, differences: Dict):
        """Compare two JSON files."""
        with open(source, "r", encoding="utf-8") as f:
            source_data = json.load(f)

        with open(output, "r", encoding="utf-8") as f:
            output_data = json.load(f)

        # Compare resources
        source_resources = source_data.get("resources", [])
        output_resources = output_data.get("resources", [])

        if len(source_resources) != len(output_resources):
            differences["structure_differences"].append(
                {
                    "type": "resource_count_mismatch",
                    "source_count": len(source_resources),
                    "output_count": len(output_resources),
                }
            )

        # Compare resource names
        source_names = {r["name"] for r in source_resources}
        output_names = {r["name"] for r in output_resources}

        missing_names = source_names - output_names
        extra_names = output_names - source_names

        if missing_names:
            differences["structure_differences"].append(
                {"type": "missing_resources", "names": sorted(list(missing_names))}
            )

        if extra_names:
            differences["structure_differences"].append(
                {"type": "extra_resources", "names": sorted(list(extra_names))}
            )

    def _compare_lk_md_dirs(self, source: Path, output: Path, differences: Dict):
        """Compare two LegendKeeper markdown directories."""
        # Similar to Notion comparison but without ID checking
        self._compare_notion_dirs(source, output, differences)

    def _compare_text_files(
        self, source_file: Path, output_file: Path, differences: Dict
    ):
        """Compare two text files and record differences."""
        source_text = source_file.read_text(encoding="utf-8")
        output_text = output_file.read_text(encoding="utf-8")

        if source_text != output_text:
            # Calculate similarity
            source_lines = source_text.splitlines()
            output_lines = output_text.splitlines()

            diff = list(
                difflib.unified_diff(
                    source_lines,
                    output_lines,
                    fromfile=str(source_file.name),
                    tofile=str(output_file.name),
                    lineterm="",
                )
            )

            differences["content_differences"].append(
                {
                    "file": str(source_file.name),
                    "diff_lines": len(diff),
                    "sample_diff": diff[:20] if diff else [],
                }
            )

    def _get_file_list(self, directory: Path, relative_to: Path) -> List[str]:
        """Get list of all files in directory, relative to base."""
        files = []
        for item in directory.rglob("*"):
            if item.is_file():
                rel_path = str(item.relative_to(relative_to))
                files.append(rel_path)
        return files

    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable test report."""
        lines = []
        lines.append("=" * 70)
        lines.append("CONVERSION TEST REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Source: {results['source']}")
        lines.append(f"Format: {results['source_format']}")
        lines.append(f"Chain:  {results['chain']}")
        lines.append(f"Time:   {results['timestamp']}")
        lines.append("")

        lines.append("CONVERSION STEPS")
        lines.append("-" * 70)
        for step in results["steps"]:
            lines.append(f"  Step {step['step']}: {step['from']} → {step['to']}")
        lines.append("")

        lines.append("DIFFERENCES SUMMARY")
        lines.append("-" * 70)
        summary = results["differences"]["summary"]
        lines.append(f"  File differences:      {summary['total_file_diffs']}")
        lines.append(f"  Content differences:   {summary['total_content_diffs']}")
        lines.append(f"  Structure differences: {summary['total_structure_diffs']}")
        lines.append("")

        # Detail file differences
        if results["differences"]["file_differences"]:
            lines.append("FILE DIFFERENCES")
            lines.append("-" * 70)
            for diff in results["differences"]["file_differences"]:
                lines.append(f"  {diff['type']}:")
                for file in diff["files"][:10]:  # Show first 10
                    lines.append(f"    - {file}")
                if len(diff["files"]) > 10:
                    lines.append(f"    ... and {len(diff['files']) - 10} more")
            lines.append("")

        # Detail content differences
        if results["differences"]["content_differences"]:
            lines.append("CONTENT DIFFERENCES")
            lines.append("-" * 70)
            for diff in results["differences"]["content_differences"][
                :5
            ]:  # Show first 5
                lines.append(f"  File: {diff['file']}")
                lines.append(f"    Changed lines: {diff['diff_lines']}")
                if diff["sample_diff"]:
                    lines.append("    Sample diff:")
                    for line in diff["sample_diff"][:10]:
                        lines.append(f"      {line}")
            if len(results["differences"]["content_differences"]) > 5:
                lines.append(
                    f"  ... and {len(results['differences']['content_differences']) - 5} more files with differences"
                )
            lines.append("")

        # Detail structure differences
        if results["differences"]["structure_differences"]:
            lines.append("STRUCTURE DIFFERENCES")
            lines.append("-" * 70)
            for diff in results["differences"]["structure_differences"]:
                lines.append(f"  {diff['type']}:")
                if "source_count" in diff:
                    lines.append(
                        f"    Source: {diff['source_count']}, Output: {diff['output_count']}"
                    )
                if "names" in diff:
                    for name in diff["names"][:10]:
                        lines.append(f"    - {name}")
                    if len(diff["names"]) > 10:
                        lines.append(f"    ... and {len(diff['names']) - 10} more")
            lines.append("")

        # Overall result
        lines.append("=" * 70)
        total_diffs = (
            summary["total_file_diffs"]
            + summary["total_content_diffs"]
            + summary["total_structure_diffs"]
        )

        if total_diffs == 0:
            lines.append("✅ RESULT: PERFECT MATCH - No differences detected!")
        elif total_diffs < 5:
            lines.append(
                f"⚠️  RESULT: MINOR DIFFERENCES - {total_diffs} differences found"
            )
        else:
            lines.append(
                f"❌ RESULT: SIGNIFICANT DIFFERENCES - {total_diffs} differences found"
            )

        lines.append("=" * 70)

        return "\n".join(lines)


def main():
    """Main entry point for testing program."""
    logger = Logger()

    if len(sys.argv) < 3:
        logger.error("❌ Invalid arguments")
        print("\nUsage:")
        print("  python3 test_converter.py <source> <conversion_chain>")
        print("\nExamples:")
        print(
            "  python3 test_converter.py testing/notion-realms notion->lk-json->notion"
        )
        print(
            "  python3 test_converter.py testing/Realms.json lk-json->notion->lk-json"
        )
        print(
            "  python3 test_converter.py testing/legendkeeper-realms lk-md->notion->lk-md"
        )
        print("\nValid formats: notion, lk-json, lk-md")
        print("Chain must start and end with same format (round-trip test)")
        sys.exit(1)

    source = Path(sys.argv[1])
    chain = sys.argv[2]

    tester = ConversionTester(logger)

    try:
        results = tester.run_test(source, chain)

        # Generate and display report
        report = tester.generate_report(results)
        print("\n" + report)

        # Save report to file
        report_dir = Path("testing/reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"test_report_{timestamp}.txt"
        report_file.write_text(report, encoding="utf-8")

        logger.success(f"✅ Report saved to: {report_file}")

        # Determine exit code
        total_diffs = (
            results["differences"]["summary"]["total_file_diffs"]
            + results["differences"]["summary"]["total_content_diffs"]
            + results["differences"]["summary"]["total_structure_diffs"]
        )

        sys.exit(0 if total_diffs == 0 else 1)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.exception(e)
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
