# NotionKeeper

Convert Notion exports (Markdown + asset folders) into a LegendKeeper-friendly structure — fast, simple, and repeatable.

🚀 Quick facts

- Purpose: Convert Notion-exported pages into a folder-per-page layout LegendKeeper can ingest.
- Language: Python
- CLI: `notionkeeper.py` (root)

✨ Highlights

- 🔎 Recursively reads Notion-exported markdown files and matching asset folders
- 🧹 Cleans page names (removes Notion IDs), strips HTML, converts callouts and todo syntax, and removes unwanted links
- 📁 Writes cleaned output into `imports/` (one folder per page) so LegendKeeper can consume it
- 📝 Writes plain-text logs to `logs/` while preserving colored console output for interactive runs

## Requirements

- Python 3.8+

## Quick start

From the repository root run the bundled CLI wrapper:

```bash
python3 notionkeeper.py --data exports --out imports
```

Or just run the default behavior (reads `exports/` and writes `imports/`):

```bash
python3 notionkeeper.py
```

## CLI options

- `--data / -d`    Path to the Notion export directory to read (default: `exports`)
- `--out  / -o`    Output path where cleaned LegendKeeper-style folders will be written (default: `imports`)
- `--no-log`       Disable writing a log file (only print to console)
- `-h / --help`    Show help and exit

## Examples

- Convert the default `exports/` folder into `imports/` (default):

```bash
python3 notionkeeper.py
```

- Convert a specific export folder and write to a different output folder:

```bash
python3 notionkeeper.py -d exports/Kaleah -o imports/Kaleah
```

## Logs

- If logging is enabled (default), a log file is written under `logs/notion_keeper_YYYYMMDD_HHMMSS.log`.

## Developer notes

- Conversion logic: `src/converter.py`
- CLI wrapper: `notionkeeper.py` (adds `src/` to PYTHONPATH and invokes the `NotionKeeper` class)

## Contributing ❤️

- Bug reports, improvements and pull requests are welcome. Please keep changes small and include a short test or example when behavior changes.

## License

- See `LICENSE` in the repository root.
