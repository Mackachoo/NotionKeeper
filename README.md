# NotionKeeper Converter

A bidirectional converter between Notion and LegendKeeper formats.

## Features

- ✅ **Notion → LegendKeeper**: Convert Notion exports (Markdown + CSV) to LegendKeeper format (JSON + Markdown)
- ✅ **LegendKeeper → Notion**: Convert LegendKeeper exports (JSON or Markdown) to Notion format
- 🧪 **Round-Trip Testing**: Automated testing program to verify conversion quality with difference analysis
- 📝 **Detailed Logging**: Colorful console output with symbols for better readability
- 💾 **File Logging**: All operations logged to timestamped files in `logs/` directory (without color codes)

## Installation

```bash
# No external dependencies required - uses Python standard library only
python --version  # Requires Python 3.7+
```

## Usage

### Convert Notion to LegendKeeper

```bash
python converter.py notion-to-lk <notion_export_dir> <output_dir>
```

Example:
```bash
python converter.py notion-to-lk exports/notion/realms/ imports/legendkeeper/
```

### Convert LegendKeeper to Notion

```bash
python converter.py lk-to-notion <lk_export> <output_dir>
```

Examples:
```bash
# From JSON export
python converter.py lk-to-notion exports/legendkeeper/Realms.json imports/notion/

# From Markdown directory
python converter.py lk-to-notion exports/legendkeeper/Realms/ imports/notion/
```

## Format Specifications

### Notion Format

Notion exports contain:
- **Markdown files** (`.md`): Pages and subpages
  - Filename format: `Page Name abc123def456.md` (includes 32-char hex ID)
  - Subdirectories contain subpages and images
- **CSV files** (`.csv`): Database tables
  - Two versions: `Name.csv` and `Name_all.csv`
  - First column is always "Name"

### LegendKeeper Format

LegendKeeper exports come in two formats:

1. **JSON Export** (`.json`):
   - Complete export with all metadata
   - Includes resources, documents, properties, tags
   - ProseMirror format for rich content

2. **Markdown Export** (directory):
   - Simplified export with folder structure
   - Hierarchical directory organization
   - Markdown files for each resource

## Project Structure

```
NotionKeeper/
├── converter.py              # Main entry point
├── src/
│   ├── __init__.py
│   ├── logger.py            # Colorful logging with file output
│   ├── models.py            # Common data models
│   ├── notion_parser.py     # Parse Notion exports
│   ├── notion_exporter.py   # Export to Notion format
│   ├── legendkeeper_parser.py   # Parse LegendKeeper exports
│   └── legendkeeper_exporter.py # Export to LegendKeeper format
├── exports/                 # Sample exports
├── imports/                 # Converted outputs
└── logs/                    # Conversion logs
```

## Data Model

The converter uses a common data model:

- **Resource**: Represents a page/entry
  - Name, ID, parent relationship
  - Content (markdown)
  - Properties (key-value pairs)
  - Tags, aliases, icons
  - Children (nested resources)

- **DatabaseRow**: Represents a database row
  - Name and properties from CSV

- **ConversionData**: Container for all data
  - Resources (hierarchical)
  - Databases (flat)
  - Metadata

## Logging

The converter provides detailed logging:

### Console Output
- 🚀 Process start
- 📂 Directory operations
- 📄 File processing
- ✅ Success messages
- ❌ Error messages
- ⚠️  Warnings
- ℹ️  Information

### Log Files
- Saved to `logs/conversion_YYYYMMDD_HHMMSS.log`
- Includes timestamps
- Full exception tracebacks
- All debug information

## Examples

### Sample Notion Export Structure
```
exports/notion/realms/
├── Realms 4685d0dc1aa74932991bf15ace69472a.md
├── Realms 4685d0dc1aa74932991bf15ace69472a_all.csv
└── Realms 4685d0dc1aa74932991bf15ace69472a/
    ├── Kaleah 9df4d446bb6f44e49bc8e4e50e13684f.md
    └── Kaleah 9df4d446bb6f44e49bc8e4e50e13684f/
        └── image.png
```

### Sample LegendKeeper Export Structure

**JSON:**
```json
{
  "version": 1,
  "resources": [
    {
      "id": "hb13iidj",
      "name": "Realms",
      "documents": [...],
      "properties": [...]
    }
  ]
}
```

**Markdown:**
```
Realms/
├── Realms.md
└── Kaleah/
    └── Kaleah.md
```

## Testing Conversions

Test conversion quality with automated round-trip testing:

```bash
python test_converter.py <source> '<conversion_chain>'
```

Examples:
```bash
# Test LegendKeeper JSON round-trip
python test_converter.py testing/Realms.json 'lk-json->notion->lk-json'

# Test Notion round-trip
python test_converter.py 'testing/notion-realms/Realms...' 'notion->lk-json->notion'
```

The testing program will:
- Run each conversion step
- Compare source with final output
- Generate detailed difference reports in `testing/reports/`
- Show ✅ Perfect, ⚠️ Minor, or ❌ Significant differences

See `docs/TESTING.md` for complete documentation.

## Documentation

- **README.md** (this file) - Overview and quick start
- **docs/EXAMPLES.md** - Detailed conversion examples with sample data
- **docs/TESTING.md** - Complete testing guide and best practices
- **docs/QUICKREF.md** - Command reference and common patterns
- **CONVERSION_RULES.py** - Technical conversion rules and specifications
- **docs/PROJECT_SUMMARY.md** - Project structure and design decisions

## NotionKeeper

A Notion to Legend Keeper converter (and maybe vice versa)
