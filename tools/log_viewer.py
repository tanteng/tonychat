#!/usr/bin/env python3
"""
Log viewer tool for TonyChat.

Supports:
- --follow / -f: Real-time log following (tail -f style)
- --request-id / -r: Filter by request_id
- --level: Filter by log level (INFO, WARNING, ERROR)
- --verbose / -v: Show all fields (full JSON)
- Color output: INFO(green), WARNING(yellow), ERROR(red)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"


LEVEL_COLORS = {
    "INFO": Colors.GREEN,
    "WARNING": Colors.YELLOW,
    "ERROR": Colors.RED,
    "DEBUG": Colors.BLUE,
}


def get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_log_path() -> str:
    """Get the path to the log file."""
    return os.path.join(get_project_root(), "logs", "tonychat.log")


def colorize_level(level: str) -> str:
    """Return colored level string."""
    color = LEVEL_COLORS.get(level.upper(), Colors.RESET)
    return f"{color}{level}{Colors.RESET}"


def format_log_entry(entry: dict[str, Any], verbose: bool = False) -> str:
    """Format a log entry for display."""
    timestamp = entry.get("timestamp", "")
    level = entry.get("level", "UNKNOWN")
    message = entry.get("message", "")
    request_id = entry.get("request_id", "")

    # Format timestamp for readability
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        pass

    if verbose:
        # Show full JSON
        return json.dumps(entry, indent=2, default=str)

    # Colorize level
    colored_level = colorize_level(level)

    # Build formatted output
    parts = [f"{Colors.GRAY}[{timestamp}]{Colors.RESET}"]

    if request_id:
        parts.append(f"{Colors.BLUE}[{request_id[:8]}]{Colors.RESET}")

    parts.append(f"{colored_level}")
    parts.append(f"- {message}")

    return " ".join(parts)


def should_display(entry: dict[str, Any], level_filter: str | None, request_id_filter: str | None) -> bool:
    """Check if entry should be displayed based on filters."""
    # Check level filter
    if level_filter:
        entry_level = entry.get("level", "").upper()
        if entry_level != level_filter.upper():
            return False

    # Check request_id filter
    if request_id_filter:
        entry_request_id = entry.get("request_id", "")
        if request_id_filter not in entry_request_id:
            return False

    return True


def read_log_entries(log_path: str, follow: bool = False) -> tuple[list[dict[str, Any]], int]:
    """Read log entries from file. Returns (entries, last_position)."""
    entries = []

    try:
        with open(log_path, "r") as f:
            content = f.read()
            if content:
                for line in content.strip().split("\n"):
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue
    except FileNotFoundError:
        print(f"Error: Log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        sys.exit(1)

    return entries, 0


def follow_log(log_path: str, level_filter: str | None, request_id_filter: str | None, verbose: bool):
    """Follow log file in real-time."""
    try:
        with open(log_path, "r") as f:
            # Seek to end
            f.seek(0, 2)

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if should_display(entry, level_filter, request_id_filter):
                    print(format_log_entry(entry, verbose))
                    sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nStopped following log.")
        sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TonyChat Log Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--follow", "-f",
        action="store_true",
        help="Follow log file in real-time (tail -f style)"
    )
    parser.add_argument(
        "--request-id", "-r",
        type=str,
        help="Filter by request_id (partial match)"
    )
    parser.add_argument(
        "--level",
        type=str,
        choices=["INFO", "WARNING", "ERROR", "DEBUG"],
        help="Filter by log level"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all fields (full JSON output)"
    )

    args = parser.parse_args()

    log_path = get_log_path()

    if args.follow:
        follow_log(log_path, args.level, args.request_id, args.verbose)
        return

    # Read and filter existing entries
    entries, _ = read_log_entries(log_path)

    # Filter entries
    filtered = [
        entry for entry in entries
        if should_display(entry, args.level, args.request_id)
    ]

    # Display entries
    if not filtered:
        print("No matching log entries found.")
        sys.exit(0)

    for entry in filtered:
        print(format_log_entry(entry, args.verbose))


if __name__ == "__main__":
    main()
