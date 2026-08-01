"""File handling utilities."""

import re
import os
from pathlib import Path


# Characters illegal in Windows/Unix filenames
_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Reserved names on Windows
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Telegram max file size: 50 MB for bots, 2 GB for premium
TELEGRAM_MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


def sanitize_filename(name: str) -> str:
    """Remove illegal characters from a filename and truncate if needed."""
    name = _ILLEGAL_CHARS.sub("_", name)
    name = name.strip(". ")
    if not name:
        name = "download"
    # Truncate to 200 chars to leave room for extension
    name = name[:200]
    return name


def format_duration(seconds: int) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    if seconds < 0:
        return "00:00"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_views(views: int) -> str:
    """Format view count with K/M/B suffixes."""
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_safe_filepath(directory: Path, filename: str, extension: str) -> Path:
    """Generate a unique file path, appending numbers if file exists."""
    base = sanitize_filename(filename)
    filepath = directory / f"{base}{extension}"
    counter = 1
    while filepath.exists():
        filepath = directory / f"{base}_{counter}{extension}"
        counter += 1
    return filepath


async def delete_file(filepath: str | Path) -> bool:
    """Safely delete a file if it exists."""
    path = Path(filepath)
    if path.exists():
        path.unlink()
        return True
    return False
