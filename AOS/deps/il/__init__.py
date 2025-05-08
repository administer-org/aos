# Copyright (c) 2025 iiPython

# Modules
import atexit
from pathlib import Path
from typing import Optional
from io import TextIOWrapper

# Version
__version__ = "0.2.3"

# Handle the log file
LOG_FILE: Optional[TextIOWrapper] = None


def cleanup_log_file() -> None:
    if LOG_FILE is not None:
        LOG_FILE.close()


def set_log_file(file: Path) -> None:
    globals()["LOG_FILE"] = file.open("a")
    atexit.register(cleanup_log_file)


# Print, but with file support


def create_log(line: str) -> None:
    print(line)
    if LOG_FILE is not None:
        LOG_FILE.write(line + "\n")
        LOG_FILE.flush()


# Begin methods


@staticmethod
def cprint(text: str, color: int) -> None:
    """Generate a line of colored text; yes, that's all it does."""
    create_log(f"\033[{color}m{text}\033[0m")


@staticmethod
def box(size: int, left: str, right: str, color: int = 34) -> None:
    """Generate a box (header) of the given size, text, and color.
    Ensure you include the sides (2 characters) in your size, as they will be subtracted.
    """
    size -= 2  # Account for sides
    create_log(f"\033[{color}m┌{'─' * size}┐")
    create_log(f"│ {left}{' ' * (size - 2 - len(left) - len(right))}{right} │")
    create_log(f"└{'─' * size}┘\033[0m")


@staticmethod
def rule(size: int, color: int = 34) -> None:
    """Generate a horizontal rule given size and color."""
    cprint("─" * size, color)


@staticmethod
def indent(text: str, color: int = 34, indent: int = 2) -> None:
    """Generate a line of indented text, meant to sit between horizontal rules."""
    cprint(f"{' ' * indent}{text}", color)


@staticmethod
def request(
    path: str,
    remote_ip: str,
    summary: str,
    summary_color: int,
    time_taken_seconds: float | int,
    detail_text: Optional[str] = None,
    verb: Optional[str] = "REQ"
) -> None:
    """Generate a log given request parameters."""
    total_time = time_taken_seconds * 1000
    # This should have 2 subtracted, but for now it's tab aligned
    spacing = " " * (len(path) - len(summary))

    create_log(f"\033[33m\u26a1 {verb} {path}\t[{remote_ip}]")
    if detail_text is not None:
        create_log(f"\033[90m   │   \033[{summary_color}m{detail_text}")

    create_log(
        f"\033[90m   └→  \033[{summary_color}m{summary}{spacing}\t\033[33m[{total_time:.1f}ms]\033[0m"
    )
