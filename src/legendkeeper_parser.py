"""
LegendKeeper Parser
==================
Parses LegendKeeper exports (JSON or Markdown files) into common data model.

LegendKeeper Export Formats:
1. JSON: Complete export with all metadata
2. Markdown: Simplified export with folder structure
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.logger import Logger
from src.models import ConversionData, Resource


class LegendKeeperParser:
    """Parser for LegendKeeper exports."""

    def __init__(self, logger: Logger):
        """Initialize parser with logger."""
        self.logger = logger

    def parse_json(self, json_file: Path) -> ConversionData:
        """
        Parse a LegendKeeper JSON export.

        Args:
            json_file: Path to LegendKeeper JSON export

        Returns:
            ConversionData containing all parsed resources
        """
        if not json_file.exists():
            raise ValueError(f"File does not exist: {json_file}")

        self.logger.info(f"📄 Reading JSON file: {json_file.name}")

        # Load JSON
        with open(json_file, "r", encoding="utf-8") as f:
            lk_data = json.load(f)

        data = ConversionData()

        # Store metadata
        data.metadata["version"] = lk_data.get("version", 1)
        data.metadata["exportId"] = lk_data.get("exportId", "")
        data.metadata["exportedAt"] = lk_data.get("exportedAt", "")

        # Parse resources
        resources_data = lk_data.get("resources", [])
        self.logger.info(f"📚 Found {len(resources_data)} resources")

        # First pass: create all resources
        resources_by_id = {}
        for res_data in resources_data:
            resource = self._parse_resource(res_data)
            resources_by_id[resource.id] = resource

        # Second pass: build hierarchy
        for resource in resources_by_id.values():
            if resource.parent_id and resource.parent_id in resources_by_id:
                parent = resources_by_id[resource.parent_id]
                parent.add_child(resource)
            else:
                # Root resource
                data.add_resource(resource)

        self.logger.info(
            f"📊 Built hierarchy with {len(data.resources)} root resources"
        )

        return data

    def parse_directory(self, directory: Path) -> ConversionData:
        """
        Parse a LegendKeeper Markdown export directory.

        Args:
            directory: Path to LegendKeeper Markdown export

        Returns:
            ConversionData containing all parsed resources
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        self.logger.info(f"📁 Scanning directory: {directory}")

        data = ConversionData()

        # Recursively parse markdown files
        root_resource = self._parse_markdown_directory(directory, None)

        if root_resource and root_resource.children:
            # If we created a wrapper, unwrap it
            for child in root_resource.children:
                data.add_resource(child)
        elif root_resource:
            data.add_resource(root_resource)

        return data

    def _parse_resource(self, res_data: Dict[str, Any]) -> Resource:
        """Parse a resource from LegendKeeper JSON."""
        # Extract basic info
        resource = Resource(
            id=res_data.get("id", ""),
            name=res_data.get("name", ""),
            parent_id=res_data.get("parentId"),
        )

        # Extract appearance
        resource.icon_glyph = res_data.get("iconGlyph")
        resource.icon_color = res_data.get("iconColor")
        resource.icon_shape = res_data.get("iconShape")
        resource.is_hidden = res_data.get("isHidden", False)
        resource.is_locked = res_data.get("isLocked", False)

        # Extract banner
        banner = res_data.get("banner", {})
        if banner.get("enabled"):
            resource.banner_url = banner.get("url", "")
            resource.banner_y_position = banner.get("yPosition", 50.0)

        # Extract tags and aliases
        resource.tags = res_data.get("tags", [])
        resource.aliases = res_data.get("aliases", [])

        # Extract properties
        properties = res_data.get("properties", [])
        for prop in properties:
            if isinstance(prop, dict):
                prop_name = prop.get("name", "")
                prop_value = prop.get("value", "")
                if prop_name:
                    resource.properties[prop_name] = prop_value

        # Extract content from documents
        documents = res_data.get("documents", [])
        resource.content = self._extract_content_from_documents(documents)

        # Store raw data for reference
        resource.raw_data = res_data

        return resource

    def _extract_content_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Extract readable content from LegendKeeper documents."""
        content_parts = []

        for doc in documents:
            doc_name = doc.get("name", "")
            doc_content = doc.get("content", {})

            # Add document name as heading
            if doc_name and doc_name != "Main":
                content_parts.append(f"# {doc_name}\n")

            # Extract content from ProseMirror format
            text = self._extract_text_from_prosemirror(doc_content)
            if text:
                content_parts.append(text)

        return "\n\n".join(content_parts)

    def _extract_text_from_prosemirror(self, content: Dict[str, Any]) -> str:
        """Extract text from ProseMirror document format."""
        if not isinstance(content, dict):
            return ""

        content_nodes = content.get("content", [])
        return self._process_nodes(content_nodes)

    def _process_nodes(self, nodes: List[Dict[str, Any]]) -> str:
        """Process ProseMirror nodes recursively."""
        parts = []

        for node in nodes:
            if not isinstance(node, dict):
                continue

            node_type = node.get("type", "")

            if node_type == "text":
                text = node.get("text", "")
                marks = node.get("marks", [])

                # Apply marks (bold, italic, etc.)
                for mark in marks:
                    mark_type = mark.get("type", "")
                    if mark_type == "strong":
                        text = f"**{text}**"
                    elif mark_type == "em":
                        text = f"*{text}*"
                    elif mark_type == "code":
                        text = f"`{text}`"
                    elif mark_type == "link":
                        href = mark.get("attrs", {}).get("href", "")
                        text = f"[{text}]({href})"

                parts.append(text)

            elif node_type == "paragraph":
                content_nodes = node.get("content", [])
                para_text = self._process_nodes(content_nodes)
                # Add blank line after paragraph for proper spacing
                parts.append(f"{para_text}\n\n")

            elif node_type == "heading":
                level = node.get("attrs", {}).get("level", 1)
                content_nodes = node.get("content", [])
                heading_text = self._process_nodes(content_nodes)
                parts.append(f"{'#' * level} {heading_text}\n")

            elif node_type == "bulletList" or node_type == "orderedList":
                list_items = node.get("content", [])
                for item in list_items:
                    item_content = item.get("content", [])
                    item_text = self._process_nodes(item_content)
                    prefix = "-" if node_type == "bulletList" else "1."
                    parts.append(f"{prefix} {item_text}\n")

            elif node_type == "listItem":
                content_nodes = node.get("content", [])
                parts.append(self._process_nodes(content_nodes))

            elif node_type == "codeBlock":
                content_nodes = node.get("content", [])
                code_text = self._process_nodes(content_nodes)
                parts.append(f"```\n{code_text}\n```\n")

            elif node_type == "blockquote":
                content_nodes = node.get("content", [])
                quote_text = self._process_nodes(content_nodes)
                parts.append(f"> {quote_text}\n")

            elif node_type == "rule":
                parts.append("---\n")

            elif node_type == "mention":
                mention_text = node.get("attrs", {}).get("text", "")
                parts.append(f"[[{mention_text}]]")

            elif node_type == "image":
                src = node.get("attrs", {}).get("src", "")
                alt = node.get("attrs", {}).get("alt", "")
                parts.append(f"![{alt}]({src})\n")

            else:
                # Try to process nested content
                content_nodes = node.get("content", [])
                if content_nodes:
                    parts.append(self._process_nodes(content_nodes))

        return "".join(parts)

    def _parse_markdown_directory(
        self, directory: Path, parent_name: Optional[str]
    ) -> Optional[Resource]:
        """Recursively parse a directory of markdown files."""
        # Look for a markdown file matching the directory name
        md_file = None
        for file in directory.iterdir():
            if file.is_file() and file.suffix == ".md":
                if parent_name is None or file.stem == directory.name:
                    md_file = file
                    break

        # Create resource for this directory
        resource_name = directory.name
        resource_id = directory.name.lower().replace(" ", "_")

        resource = Resource(id=resource_id, name=resource_name)

        # Read content if markdown file exists
        if md_file:
            resource.content = md_file.read_text(encoding="utf-8")
            self.logger.item(f"Parsed: {md_file.name}")

        # Process subdirectories
        for subdir in sorted(directory.iterdir()):
            if subdir.is_dir():
                child = self._parse_markdown_directory(subdir, resource_name)
                if child:
                    resource.add_child(child)

        # Process other markdown files in this directory
        for file in sorted(directory.iterdir()):
            if file.is_file() and file.suffix == ".md" and file != md_file:
                child_resource = Resource(
                    id=file.stem.lower().replace(" ", "_"),
                    name=file.stem,
                    content=file.read_text(encoding="utf-8"),
                )
                resource.add_child(child_resource)
                self.logger.item(f"Parsed: {file.name}")

        return resource
