"""
Notion Exporter
==============
Exports data to Notion format (Markdown + CSV files).
"""

import csv
from pathlib import Path
from typing import Dict, List

from src.logger import Logger
from src.models import ConversionData, Resource, DatabaseRow


class NotionExporter:
    """Exporter for Notion format."""

    def __init__(self, logger: Logger):
        """Initialize exporter with logger."""
        self.logger = logger

    def export(self, data: ConversionData, output_dir: Path):
        """
        Export data to Notion format.

        Args:
            data: ConversionData to export
            output_dir: Directory to write Notion files
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"📁 Creating output directory: {output_dir}")

        # Export databases as CSV files
        for db_name, rows in data.databases.items():
            self._export_database(db_name, rows, output_dir)

        # Export resources as markdown files
        for resource in data.resources:
            self._export_resource(resource, output_dir)

        self.logger.success(f"✅ Exported to {output_dir}")

    def _export_database(self, db_name: str, rows: List[DatabaseRow], output_dir: Path):
        """Export a database to CSV files."""
        if not rows:
            return

        # Generate filename
        csv_filename = f"{db_name}.csv"
        csv_all_filename = f"{db_name}_all.csv"

        # Get all column names
        columns = set(["Name"])
        for row in rows:
            columns.update(row.properties.keys())

        columns = ["Name"] + sorted([c for c in columns if c != "Name"])

        # Write CSV
        csv_path = output_dir / csv_filename
        csv_all_path = output_dir / csv_all_filename

        for path in [csv_path, csv_all_path]:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

                for row in rows:
                    row_dict = {"Name": row.name}
                    row_dict.update(row.properties)
                    writer.writerow(row_dict)

        self.logger.item(f"Exported database: {csv_filename} ({len(rows)} rows)")

    def _export_resource(self, resource: Resource, output_dir: Path):
        """Export a resource and its children as markdown files."""
        # Create markdown filename
        md_filename = f"{resource.name} {resource.id}.md"
        md_path = output_dir / md_filename

        # Write content
        content = self._format_content(resource)
        md_path.write_text(content, encoding="utf-8")

        self.logger.item(f"Exported page: {md_filename}")

        # Create subdirectory for children if any
        if resource.children:
            subdir = output_dir / f"{resource.name} {resource.id}"
            subdir.mkdir(parents=True, exist_ok=True)

            for child in resource.children:
                self._export_resource(child, subdir)

    def _format_content(self, resource: Resource) -> str:
        """Format resource content for Notion markdown."""
        parts = []

        # Add title
        parts.append(f"# {resource.name}\n")

        # Add properties if any (preserve insertion order)
        if resource.properties:
            for key, value in resource.properties.items():
                parts.append(f"{key}: {value}")
            parts.append("")

        # Add main content
        if resource.content:
            parts.append(resource.content)

        # Add tags if any
        if resource.tags:
            parts.append(f"\nTags: {', '.join(resource.tags)}")

        return "\n".join(parts)
