"""
LegendKeeper Exporter
====================
Exports data to LegendKeeper format (JSON or Markdown files).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.logger import Logger
from src.models import ConversionData, Resource


class LegendKeeperExporter:
    """Exporter for LegendKeeper format."""

    def __init__(self, logger: Logger):
        """Initialize exporter with logger."""
        self.logger = logger

    def export(self, data: ConversionData, output_dir: Path):
        """
        Export data to LegendKeeper format.

        Creates both JSON and Markdown exports.

        Args:
            data: ConversionData to export
            output_dir: Directory to write LegendKeeper files
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"📁 Creating output directory: {output_dir}")

        # Determine root name
        root_name = "Export"
        if data.resources:
            root_name = data.resources[0].name

        # Export as JSON
        json_path = output_dir / f"{root_name}.json"
        self._export_json(data, json_path)

        # Export as Markdown directory
        md_dir = output_dir / root_name
        self._export_markdown(data, md_dir)

        self.logger.success(f"✅ Exported to {output_dir}")

    def _export_json(self, data: ConversionData, json_path: Path):
        """Export data as LegendKeeper JSON."""
        # Build JSON structure
        lk_data = {
            "version": data.metadata.get("version", 1),
            "exportId": data.metadata.get("exportId", self._generate_id()),
            "exportedAt": data.metadata.get(
                "exportedAt", datetime.now().isoformat() + "Z"
            ),
            "resources": [],
            "calendars": [],
            "resourceCount": 0,
            "hash": "",
        }

        # Convert resources to LegendKeeper format
        all_resources = data.get_all_resources()
        for resource in all_resources:
            lk_resource = self._resource_to_legendkeeper(resource)
            lk_data["resources"].append(lk_resource)

        lk_data["resourceCount"] = len(all_resources)

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(lk_data, f, indent=2, ensure_ascii=False)

        self.logger.item(
            f"Exported JSON: {json_path.name} ({len(all_resources)} resources)"
        )

    def _export_markdown(self, data: ConversionData, md_dir: Path):
        """Export data as LegendKeeper Markdown directory."""
        md_dir.mkdir(parents=True, exist_ok=True)

        # Export each resource
        for resource in data.resources:
            self._export_resource_markdown(resource, md_dir)

        self.logger.item(f"Exported Markdown directory: {md_dir.name}")

    def _export_resource_markdown(self, resource: Resource, parent_dir: Path):
        """Export a resource and its children as markdown files."""
        # Create markdown file
        md_path = parent_dir / f"{resource.name}.md"

        # Format content
        content = self._format_markdown_content(resource)
        md_path.write_text(content, encoding="utf-8")

        # Create subdirectory for children if any
        if resource.children:
            subdir = parent_dir / resource.name
            subdir.mkdir(parents=True, exist_ok=True)

            for child in resource.children:
                self._export_resource_markdown(child, subdir)

    def _format_markdown_content(self, resource: Resource) -> str:
        """Format resource content as markdown."""
        parts = []

        # Add frontmatter if there are tags
        if resource.tags:
            parts.append("---")
            parts.append(f"tags: {', '.join(resource.tags)}")
            parts.append("---")
            parts.append("")

        # Add content
        if resource.content:
            # Remove leading title if it matches resource name
            content = resource.content
            if content.startswith(f"# {resource.name}"):
                content = content[len(f"# {resource.name}") :].lstrip()
            parts.append(content)

        return "\n".join(parts)

    def _resource_to_legendkeeper(self, resource: Resource) -> Dict[str, Any]:
        """Convert a Resource to LegendKeeper JSON format."""
        lk_resource = {
            "schemaVersion": 1,
            "id": resource.id,
            "name": resource.name,
            "aliases": resource.aliases,
            "tags": resource.tags,
            "isHidden": resource.is_hidden,
            "isLocked": resource.is_locked,
            "showPropertyBar": True,
            "properties": [],
            "documents": [],
            "createdBy": "converter",
            "pos": "M",
        }

        # Add parent ID if exists
        if resource.parent_id:
            lk_resource["parentId"] = resource.parent_id

        # Add icon
        if resource.icon_glyph or resource.icon_color or resource.icon_shape:
            lk_resource["iconGlyph"] = resource.icon_glyph or "book"
            lk_resource["iconColor"] = resource.icon_color or "#C49454"
            lk_resource["iconShape"] = resource.icon_shape or "pin-medium"
        else:
            lk_resource["iconGlyph"] = "book"
            lk_resource["iconColor"] = "#C49454"
            lk_resource["iconShape"] = "pin-medium"

        # Add banner
        lk_resource["banner"] = {
            "enabled": bool(resource.banner_url),
            "url": resource.banner_url or "",
            "yPosition": resource.banner_y_position,
        }

        # Convert properties
        for key, value in resource.properties.items():
            lk_resource["properties"].append({"name": key, "value": value})

        # Convert content to document
        if resource.content:
            doc = self._content_to_document(resource.content, "Main")
            lk_resource["documents"].append(doc)

        return lk_resource

    def _content_to_document(self, content: str, name: str) -> Dict[str, Any]:
        """Convert markdown content to LegendKeeper document format."""
        # Convert markdown to ProseMirror nodes
        nodes = self._markdown_to_prosemirror(content)

        return {
            "id": self._generate_id(),
            "pos": "O",
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "updatedAt": datetime.utcnow().isoformat() + "Z",
            "locatorId": f"document:{self._generate_id()}",
            "name": name,
            "type": "page",
            "isHidden": False,
            "isFullWidth": False,
            "isFirst": True,
            "transforms": [],
            "sources": [],
            "presentation": {"documentType": "page"},
            "content": {"type": "doc", "content": nodes},
        }

    def _markdown_to_prosemirror(self, content: str) -> List[Dict[str, Any]]:
        """Convert markdown content to ProseMirror nodes."""
        nodes = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]

            # Empty lines are just skipped - paragraph breaks are handled by grouping text
            if not line.strip():
                i += 1
                continue

            # Headings
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("#").strip()
                nodes.append(
                    {
                        "type": "heading",
                        "attrs": {"level": min(level, 6)},
                        "content": [{"type": "text", "text": text}],
                    }
                )

            # Horizontal rule
            elif line.strip() in ["---", "***", "___"]:
                nodes.append({"type": "rule"})

            # Bullet list
            elif line.strip().startswith(("-", "*", "+")):
                text = line.strip()[1:].strip()
                nodes.append(
                    {
                        "type": "bulletList",
                        "content": [
                            {
                                "type": "listItem",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": text}],
                                    }
                                ],
                            }
                        ],
                    }
                )

            # Blockquote
            elif line.strip().startswith(">"):
                text = line.strip()[1:].strip()
                nodes.append(
                    {
                        "type": "blockquote",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": text}],
                            }
                        ],
                    }
                )

            # Image
            elif line.strip().startswith("!["):
                # Extract alt and src
                import re

                match = re.match(r"!\[(.*?)\]\((.*?)\)", line.strip())
                if match:
                    alt, src = match.groups()
                    nodes.append(
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": f"![{alt}]({src})"}],
                        }
                    )

            # Regular paragraph
            else:
                # Collect consecutive non-empty text lines into one paragraph
                para_lines = [line]
                i += 1
                while (
                    i < len(lines)
                    and lines[i].strip()
                    and not self._is_special_line(lines[i])
                ):
                    para_lines.append(lines[i])
                    i += 1

                # Join lines with space (they're part of same paragraph)
                para_text = " ".join(para_lines)
                nodes.append(
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": para_text}],
                    }
                )
                continue  # Don't increment i again

            i += 1

        return nodes

    def _is_special_line(self, line: str) -> bool:
        """Check if line is a special markdown element (heading, list, etc.)."""
        stripped = line.strip()
        return (
            stripped.startswith("#")
            or stripped.startswith(("-", "*", "+"))
            or stripped.startswith(">")
            or stripped.startswith("![")
            or stripped in ["---", "***", "___"]
        )

    def _generate_id(self) -> str:
        """Generate a simple ID for LegendKeeper resources."""
        import random
        import string

        chars = string.ascii_lowercase + string.digits
        return "".join(random.choice(chars) for _ in range(8))
