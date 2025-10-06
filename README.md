# NotionKeeper

NotionKeeper converts a Notion export (markdown + asset folders) into a structure suitable for LegendKeeper.

This repository contains the conversion logic in `src/` and a small CLI wrapper at the project root for convenient command-line use.

Features

- Recursively reads Notion-exported markdown files and matching folders.
- Cleans Notion IDs from page names, removes HTML, converts callouts and todo syntax, and strips links.
- Writes the cleaned output into a folder-per-page layout that LegendKeeper can ingest.
- Produces a plain-text log (color codes stripped) in `logs/` while keeping colored console output.

Requirements

- Python 3.8+
- tqdm (for progress display)

Install

Install the small dependency used by the tool:

```bash
python3 -m pip install --upgrade tqdm
```

Quick usage (recommended)

From the repository root you can run the bundled CLI wrapper:

```bash
python3 notionkeeper.py --data exports --out imports
```

Options

- --data / -d    Path to the Notion export directory to read (default: `exports`)
- --out  / -o    Output path where cleaned LegendKeeper-style folders will be written (default: `imports`)
- --no-log       Disable writing a log file and only print to the console
- -h / --help    Show help and exit

Examples

- Convert the default `exports/` folder into `imports/` (default behavior):

```bash
python3 notionkeeper.py
```

- Convert a specific export folder and write to a different output folder:

```bash
python3 notionkeeper.py -d exports/Kaleah -o imports/Kaleah
```

Log files

- If logging is enabled (default), a log file is written under `logs/notion_keeper_YYYYMMDD_HHMMSS.log`.

Developer notes

- The conversion logic lives in `src/converter.py`. The root `notionkeeper.py` is a small wrapper that inserts `src/` on the Python path and calls the `NotionKeeper` class.

Contributing

- Bug reports, improvements and pull requests are welcome. Keep changes small and add a short test or example when behavior changes.

License

- See `LICENSE` in the repository root.
