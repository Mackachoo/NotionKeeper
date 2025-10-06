from datetime import datetime
import os
import re
import sys
from element import Element
from utils import Colors, Logger
from typing import List


class NotionKeeper:

    def __init__(self, data_path: str) -> None:
        """Initialize NotionKeeper with paths and logging."""
        self.data_path = data_path

        # Initialize Logger
        date = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = f"logs/notion_keeper_{date}.log"
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.logger = None

    def start_logging(self):
        """Start dual output to console and log file"""
        self.logger = Logger(self.log_path)
        sys.stdout = self.logger
        print(
            f"{Colors.OKCYAN}📝 NotionKeeper logging started: {self.log_path}{Colors.ENDC}"
        )

    def stop_logging(self):
        """Stop logging and restore normal console output"""
        if self.logger:
            print(
                f"{Colors.OKCYAN}📝 NotionKeeper log saved to: {self.log_path}{Colors.ENDC}"
            )
            sys.stdout = self.logger.stdout
            self.logger.close()
            self.logger = None

    # * Element Handling *#

    def read_notion_elements(self, directory_path: str) -> List[Element]:
        """Recursively read Notion export files and create Element objects."""
        elements = []

        # Get all items in the directory
        try:
            items = os.listdir(directory_path)
        except Exception as e:
            print(
                f"{Colors.FAIL}❌ Error reading directory {directory_path}: {e}{Colors.ENDC}"
            )
            return elements

        # Track which directories have been processed
        processed_dirs = set()

        # Process all markdown files
        for item in items:
            item_path = os.path.join(directory_path, item)

            # Only process markdown files and skip if it's a directory (we'll process it later if it matches a markdown file)
            if not item.endswith(".md") or os.path.isdir(item_path):
                continue

            # Extract the file name without extension to use as element name
            element_name = os.path.splitext(item)[0]

            # Read the file contents
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(
                    f"{Colors.FAIL}❌ Error reading file {item_path}: {e}{Colors.ENDC}"
                )
                continue

            # Create the element
            element = Element(name=element_name, context=content)

            # Check if there's a directory with the same name (without .md extension)
            corresponding_dir = os.path.join(directory_path, element_name)

            if os.path.isdir(corresponding_dir):
                # Recursively read subelements from the corresponding directory
                element.subelements = self.read_notion_elements(corresponding_dir)
                processed_dirs.add(element_name)

            elements.append(element)

        # Process any remaining directories that weren't paired with a markdown file
        for item in items:
            item_path = os.path.join(directory_path, item)

            # Check if it's a directory and hasn't been processed yet
            if os.path.isdir(item_path) and item not in processed_dirs:
                # Create an element with blank content
                element = Element(name=item, context="")

                # Recursively read subelements from this directory
                element.subelements = self.read_notion_elements(item_path)

                elements.append(element)

        return elements

    def save_legendkeeper_elements(
        self, export_path: str, elements: List[Element]
    ) -> None:
        """Recursively save elements to LegendKeeper format."""
        os.makedirs(export_path, exist_ok=True)

        for element in elements:
            # Create a directory for the element
            element_dir = os.path.join(export_path, element.name)
            os.makedirs(element_dir, exist_ok=True)

            # Save the element's context to a markdown file
            file_path = os.path.join(export_path, f"{element.name}.md")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(element.context)
            except Exception as e:
                print(
                    f"{Colors.FAIL}❌ Error writing file {file_path}: {e}{Colors.ENDC}"
                )

            # Recursively save subelements inside this element's directory
            if element.subelements:
                self.save_legendkeeper_elements(element_dir, element.subelements)

    def print_elements(self, elements: List[Element], indent: int = 0) -> None:
        """Recursively print elements and their subelements for debugging."""
        for element in elements:
            print(" " * indent + f"{Colors.OKBLUE}• {element.name}{Colors.ENDC}")
            if element.subelements:
                self.print_elements(element.subelements, indent + 4)

    def len_elements(self, elements: List[Element]) -> int:
        """Recursively count total number of elements and subelements."""
        total = 0
        for element in elements:
            total += 1  # Count the element itself
            if element.subelements:
                total += self.len_elements(element.subelements)  # Count subelements
        return total

    def map_all_elements(
        self, elements: List[Element], functions: List[callable]
    ) -> None:
        """Apply functions to all elements and their subelements in place."""
        for element in elements:
            for function in functions:
                function(element)
            # Recursively apply to subelements
            if element.subelements:
                self.map_all_elements(element.subelements, functions)

    # * LegendKeeper Conversion Rules *#

    def clean_notion_ids(self, element: Element) -> None:
        """Remove Notion IDs from element names."""
        try:
            # Notion IDs are typically 32-character hex strings, often at the end of the name
            # They are separated by a space, not a dash
            element.name = re.sub(r"\s+[0-9a-fA-F]{32}$", "", element.name)
        except Exception as e:
            print(
                f"{Colors.FAIL}❌ Error cleaning Notion ID from {element.name}: {e}{Colors.ENDC}"
            )

    def convert_callouts(self, element: Element) -> None:
        """Convert Notion callouts to LegendKeeper format."""
        try:
            # Example: Convert Notion callout syntax to LegendKeeper format
            element.context = re.sub(r"<\/?aside>", "!!!", element.context)
        except Exception as e:
            print(
                f"{Colors.FAIL}❌ Error converting callouts in {element.name}: {e}{Colors.ENDC}"
            )

    def clean_html_tags(self, element: Element) -> None:
        """Remove HTML tags from element context."""
        try:
            element.context = re.sub(r"<[^>]+>", "", element.context)
        except Exception as e:
            print(
                f"{Colors.FAIL}❌ Error removing HTML tags in {element.name}: {e}{Colors.ENDC}"
            )

    def convert_todos(self, element: Element) -> None:
        """Convert Notion to-do lists to LegendKeeper format."""
        try:
            # Example: Convert Notion to-do syntax to LegendKeeper format
            element.context = re.sub(r"- \[ \]", "- [ ]", element.context)  # Unchecked
            element.context = re.sub(r"- \[x\]", "- [x]", element.context)  # Checked
        except Exception as e:
            print(
                f"{Colors.FAIL}❌ Error converting to-dos in {element.name}: {e}{Colors.ENDC}"
            )

    def remove_links(self, element: Element) -> None:
        """Remove hyperlinks from element context."""
        try:
            # Example: Remove markdown links but keep the link text
            element.context = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", element.context)
            element.context = re.sub(r"\(https[\w\/:.%\-\?=]*\)", "", element.context)
            element.context = re.sub(r"\(..\/[\w\/:.%\-\?=]*\)", "", element.context)
        except Exception as e:
            print(
                f"{Colors.FAIL}❌ Error removing links in {element.name}: {e}{Colors.ENDC}"
            )

    # * Main Conversion Process *#

    def to_legendkeeper(self, export_path: str) -> None:
        """Convert Notion export to LegendKeeper format."""
        print(
            f"{Colors.HEADER}{Colors.BOLD}✨ Converting Notion → LegendKeeper{Colors.ENDC}\n"
        )

        # Read all files and convert to DirectoryData
        print(f"{Colors.OKCYAN}📖 Parsing Notion files{Colors.ENDC}\n")
        root_elements = self.read_notion_elements(self.data_path)

        print(f"{Colors.OKCYAN}🔍 Read elements:{Colors.ENDC}\n")
        self.print_elements(root_elements)  # For demonstration purposes

        print(
            f"\n{Colors.WARNING}📋 Total elements to clean: {self.len_elements(root_elements)}{Colors.ENDC}\n"
        )

        print(f"{Colors.HEADER}🚀 Applying following rules:{Colors.ENDC}")
        functions = []

        print(f"{Colors.GRAY}\t• Cleaning notions ids from name{Colors.ENDC}")
        functions.append(self.clean_notion_ids)
        print(f"{Colors.GRAY}\t• Converting callouts{Colors.ENDC}")
        functions.append(self.convert_callouts)
        print(f"{Colors.GRAY}\t• Clean HTML tags{Colors.ENDC}")
        functions.append(self.clean_html_tags)
        print(f"{Colors.GRAY}\t• Converting to-dos{Colors.ENDC}")
        functions.append(self.convert_todos)
        print(f"{Colors.GRAY}\t• Removing links{Colors.ENDC}")
        functions.append(self.remove_links)
        print("\n")

        # Apply all functions to all elements in place
        self.map_all_elements(root_elements, functions, None)

        print(f"\n{Colors.OKCYAN}🔍 Cleaned elements:{Colors.ENDC}\n")
        self.print_elements(root_elements)  # For demonstration purposes

        print(f"\n{Colors.OKCYAN}💾 Saving cleaned elements...{Colors.ENDC}")
        self.save_legendkeeper_elements(
            export_path,
            root_elements,
        )
        print(f"{Colors.OKGREEN}✅ Saved cleaned elements{Colors.ENDC}\n")

        print(f"{Colors.HEADER}{Colors.BOLD}✨ Conversion complete!{Colors.ENDC}\n")


if __name__ == "__main__":
    nk = NotionKeeper(data_path="exports")
    nk.start_logging()
    nk.to_legendkeeper(export_path="imports")
    nk.stop_logging()
