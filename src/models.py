"""
Data models for the converter.
Provides common data structures used by both parsers and exporters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Resource:
    """Represents a page/resource in the knowledge base."""

    id: str
    name: str
    parent_id: Optional[str] = None

    # Content
    content: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)

    # Appearance
    icon_glyph: Optional[str] = None
    icon_color: Optional[str] = None
    icon_shape: Optional[str] = None
    banner_url: Optional[str] = None
    banner_y_position: float = 50.0

    # State
    is_hidden: bool = False
    is_locked: bool = False

    # Children
    children: List["Resource"] = field(default_factory=list)

    # Images and attachments
    images: List[str] = field(default_factory=list)

    # Original data for reference
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: "Resource"):
        """Add a child resource."""
        self.children.append(child)
        child.parent_id = self.id

    def get_path(self) -> List[str]:
        """Get the path from root to this resource as a list of names."""
        path = [self.name]
        # This would need parent reference to build full path
        return path


@dataclass
class DatabaseRow:
    """Represents a row in a Notion database (CSV)."""

    name: str
    properties: Dict[str, str] = field(default_factory=dict)
    raw_data: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConversionData:
    """Container for all data being converted."""

    # Root resources (pages without parents)
    resources: List[Resource] = field(default_factory=list)

    # Database rows (from CSVs)
    databases: Dict[str, List[DatabaseRow]] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_resource(self, resource: Resource):
        """Add a root-level resource."""
        self.resources.append(resource)

    def add_database(self, name: str, rows: List[DatabaseRow]):
        """Add a database with its rows."""
        self.databases[name] = rows

    def find_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Find a resource by its ID recursively."""

        def search(resources: List[Resource]) -> Optional[Resource]:
            for resource in resources:
                if resource.id == resource_id:
                    return resource
                found = search(resource.children)
                if found:
                    return found
            return None

        return search(self.resources)

    def find_resource_by_name(self, name: str) -> Optional[Resource]:
        """Find a resource by its name recursively."""

        def search(resources: List[Resource]) -> Optional[Resource]:
            for resource in resources:
                if resource.name == name:
                    return resource
                found = search(resource.children)
                if found:
                    return found
            return None

        return search(self.resources)

    def get_all_resources(self) -> List[Resource]:
        """Get all resources as a flat list."""

        def collect(resources: List[Resource]) -> List[Resource]:
            result = []
            for resource in resources:
                result.append(resource)
                result.extend(collect(resource.children))
            return result

        return collect(self.resources)
