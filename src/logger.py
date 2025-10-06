"""
Logger module for NotionKeeper converter.
Provides colorful console output and file logging.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[37m",  # White
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "SUCCESS": "\033[32m",  # Green
        "SECTION": "\033[1;34m",  # Bold Blue
        "STEP": "\033[1;36m",  # Bold Cyan
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, *args, use_colors=True, **kwargs):
        """Initialize formatter with optional color support."""
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors

    def format(self, record):
        """Format log record with optional colors."""
        if self.use_colors:
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            reset = self.COLORS["RESET"]

            # Add color to the message
            record.msg = f"{color}{record.msg}{reset}"

        return super().format(record)


class Logger:
    """Logger class with colorful output and file logging."""

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize logger.

        Args:
            log_file: Optional path to log file. If None, uses default location.
        """
        # Create logs directory if it doesn't exist
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"conversion_{timestamp}.log"

        self.log_file = log_file

        # Setup logger
        self.logger = logging.getLogger("NotionKeeper")
        self.logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        self.logger.handlers = []

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter("%(message)s", use_colors=True)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler without colors
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            use_colors=False,
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Log initial message
        self.info(f"📝 Logging to: {log_file}")

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(f"🔍 {message}")

    def info(self, message: str):
        """Log info message."""
        self.logger.info(f"ℹ️  {message}")

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"⚠️  {message}")

    def error(self, message: str):
        """Log error message."""
        self.logger.error(f"❌ {message}")

    def success(self, message: str):
        """Log success message."""
        # Create custom log level for success
        self.logger.log(25, f"✅ {message}")

    def section(self, message: str):
        """Log section header."""
        separator = "═" * 60
        self.logger.info("")
        self.logger.info(separator)
        self.logger.info(f"  {message}")
        self.logger.info(separator)

    def step(self, message: str):
        """Log step in process."""
        self.logger.info(f"\n▶️  {message}")

    def item(self, message: str):
        """Log item in a list."""
        self.logger.info(f"  • {message}")

    def exception(self, exc: Exception):
        """Log exception with full traceback."""
        self.logger.exception("Exception details:", exc_info=exc)
