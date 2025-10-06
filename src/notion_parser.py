"""
Notion Parser
============
Parses Notion exports (Markdown + CSV files) into common data model.

Notion Export Format:
- Pages are exported as .md files
- Databases are exported as .csv files
- Files include unique IDs in their names (e.g., "Page Name abc123.md")
- Subdirectories contain subpages and assets
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

from src.logger import Logger
from src.models import ConversionData, Resource, DatabaseRow


class NotionParser:
    """Parser for Notion exports."""

    def __init__(self, logger: Logger):
        """Initialize parser with logger."""
        self.logger = logger

    def parse_directory(self, directory: Path) -> ConversionData:
        """
        Parse a Notion export directory.

        Args:
            directory: Path to Notion export directory

        Returns:
            ConversionData containing all parsed resources
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        data = ConversionData()

        # Find all markdown and CSV files
        md_files = list(directory.glob("*.md"))
        csv_files = list(directory.glob("*_all.csv"))

        self.logger.info(f"📄 Found {len(md_files)} markdown files")
        self.logger.info(f"📊 Found {len(csv_files)} CSV files")

        # Parse CSV files (databases)
        for csv_file in csv_files:
            self.logger.item(f"Parsing CSV: {csv_file.name}")
            rows = self._parse_csv(csv_file)
            db_name = self._extract_name_from_filename(
                csv_file.stem.replace("_all", "")
            )
            data.add_database(db_name, rows)

        # Parse markdown files (pages)
        for md_file in md_files:
            self.logger.item(f"Parsing page: {md_file.name}")
            resource = self._parse_page(md_file, directory)
            if resource:
                data.add_resource(resource)

        return data

    def _parse_page(self, md_file: Path, base_dir: Path) -> Optional[Resource]:
        """Parse a Notion page markdown file."""
        # Extract name and ID from filename
        name = self._extract_name_from_filename(md_file.stem)
        page_id = self._extract_id_from_filename(md_file.stem)

        # Read content
        content = md_file.read_text(encoding="utf-8")

        # Create resource
        resource = Resource(id=page_id, name=name, content=content)

        # Look for subdirectory with same name (contains subpages and images)
        subdir = md_file.parent / md_file.stem
        if subdir.exists() and subdir.is_dir():
            self._parse_subpages(resource, subdir)
            self._find_images(resource, subdir)

        # Extract properties from markdown
        self._extract_properties(resource)

        return resource

    def _parse_subpages(self, parent: Resource, subdir: Path):
        """Parse subpages from a subdirectory."""
        # Find markdown files (subpages)
        for md_file in subdir.glob("*.md"):
            child = self._parse_page(md_file, subdir)
            if child:
                parent.add_child(child)

    def _find_images(self, resource: Resource, subdir: Path):
        """Find images and attachments in subdirectory."""
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

        for file in subdir.iterdir():
            if file.is_file() and file.suffix.lower() in image_extensions:
                resource.images.append(str(file))

    def _parse_csv(self, csv_file: Path) -> List[DatabaseRow]:
        """Parse a Notion database CSV file."""
        rows = []

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_data in reader:
                if "Name" in row_data:
                    row = DatabaseRow(
                        name=row_data["Name"],
                        properties={k: v for k, v in row_data.items() if k != "Name"},
                        raw_data=dict(row_data),
                    )
                    rows.append(row)

        return rows

    def _extract_name_from_filename(self, filename: str) -> str:
        """
        Extract page name from Notion filename.

        Notion format: "Page Name abc123def456.md"
        Returns: "Page Name"
        """
        # Remove the ID (32 hex characters) from the end
        match = re.match(r"^(.+?)\s+[a-f0-9]{32}$", filename)
        if match:
            return match.group(1).strip()

        # If no ID found, return the whole filename
        return filename

    def _extract_id_from_filename(self, filename: str) -> str:
        """
        Extract ID from Notion filename.

        Notion format: "Page Name abc123def456.md"
        Returns: "abc123def456"
        """
        # Extract the ID (32 hex characters) from the end
        match = re.search(r"[a-f0-9]{32}$", filename)
        if match:
            return match.group(0)

        # Generate a simple ID if not found
        return filename.lower().replace(" ", "_")

    def _extract_properties(self, resource: Resource):
        """Extract properties from markdown content and remove them from content."""
        lines = resource.content.split("\n")
        content_start_idx = 0

        # Skip the first heading (title) - it's always line 0 in Notion exports
        if lines and lines[0].strip().startswith("# "):
            content_start_idx = 1

        # Skip empty line after title if present
        if content_start_idx < len(lines) and lines[content_start_idx].strip() == "":
            content_start_idx += 1

        # Extract properties from lines immediately after title
        property_end_idx = content_start_idx
        for i in range(content_start_idx, min(content_start_idx + 20, len(lines))):
            line = lines[i].strip()

            # Empty line after properties marks end of property section
            if line == "":
                if property_end_idx > content_start_idx:
                    # We found properties, this empty line ends the section
                    property_end_idx = i + 1
                    break
                else:
                    # Empty line before any properties, keep searching
                    continue

            # Check if this looks like a property line
            match = re.match(r"^([A-Z][a-zA-Z\s]+):\s+(.+)$", line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                resource.properties[key] = value
                property_end_idx = i + 1
            else:
                # Non-property, non-empty line found - end of properties
                if property_end_idx > content_start_idx:
                    break

        # Update resource content to exclude title and properties
        # Keep all content from after the property section
        resource.content = "\n".join(lines[property_end_idx:]).strip()
