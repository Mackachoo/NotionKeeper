#!/usr/bin/env python3
"""
Shared utilities for NotionKeeper
Contains logging and color utilities used across multiple scripts
"""

import sys
import re


class Logger:
    """Dual output to console and log file, with color stripping for file output"""

    def __init__(self, log_file_path: str):
        self.log_file = open(log_file_path, "w", encoding="utf-8", buffering=1)
        self.stdout = sys.stdout

    def write(self, message):
        # Write to console with colors
        self.stdout.write(message)
        if "\n" in message:
            self.stdout.flush()

        # Strip ANSI color codes for log file and write
        clean_message = re.sub(r"\033\[[0-9;]*m", "", message)
        self.log_file.write(clean_message)
        if "\n" in message:
            self.log_file.flush()

    def flush(self):
        self.stdout.flush()
        self.log_file.flush()

    def close(self):
        if hasattr(self, "log_file") and self.log_file:
            self.log_file.close()

    def __del__(self):
        self.close()


# ANSI color codes for console output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    GRAY = "\033[90m"
