#!/usr/bin/env python3
"""
Safely remove orphaned local gallery references from data/events.json.

Behavior:
- Keeps Cloudinary gallery objects unchanged.
- Keeps legacy {"image": "..."} objects unchanged.
- Keeps local {"url": "images/..."} objects when the referenced file exists.
- Removes only local URL objects whose file is missing from app/static/.
- Creates a timestamped backup before writing.
- Runs in dry-run mode unless --apply is supplied.

Run from the project root:
    python cleanup_orphaned_gallery.py
    python cleanup_orphaned_gallery.py --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
EVENTS_PATH = PROJECT_ROOT / "data" / "events.json"
STATIC_ROOT = PROJECT_ROOT / "app" / "static"


def is_remote_url(value: str) -> bool:
    return value.startswith(("https://", "http://"))


def inspect_events(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    cleaned_events: list[dict[str, Any]] = []
    messages: list[str] = []

    for event in events:
        cleaned_event = dict(event)
        gallery = event.get("gallery", [])

        if not isinstance(gallery, list):
            messages.append(
                f"[WARN] {event.get('slug', '<unknown>')}: gallery is not a list; left unchanged."
            )
            cleaned_events.append(cleaned_event)
            continue

        cleaned_gallery: list[Any] = []

        for index, item in enumerate(gallery):
            if not isinstance(item, dict):
                cleaned_gallery.append(item)
                messages.append(
                    f"[WARN] {event.get('slug', '<unknown>')} gallery[{index}]: "
                    "not an object; left unchanged."
                )
                continue

            if "image" in item and "url" not in item:
                cleaned_gallery.append(item)
                continue

            url = item.get("url")

            if isinstance(url, str) and is_remote_url(url):
                cleaned_gallery.append(item)
                continue

            if isinstance(url, str) and url:
                local_path = STATIC_ROOT / url.lstrip("/")

                if local_path.is_file():
                    cleaned_gallery.append(item)
                else:
                    messages.append(
                        f"[REMOVE] {event.get('slug', '<unknown>')} gallery[{index}]: "
                        f"{url} (missing: {local_path})"
                    )
                continue

            cleaned_gallery.append(item)
            messages.append(
                f"[WARN] {event.get('slug', '<unknown>')} gallery[{index}]: "
                "unrecognized structure; left unchanged."
            )

        cleaned_event["gallery"] = cleaned_gallery
        cleaned_events.append(cleaned_event)

    return cleaned_events, messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove only missing local gallery references from events.json."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the cleaned JSON. Without this flag, only show a preview.",
    )
    args = parser.parse_args()

    if not EVENTS_PATH.is_file():
        print(f"ERROR: Could not find {EVENTS_PATH}")
        return 1

    try:
        events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: Could not read valid JSON from {EVENTS_PATH}: {error}")
        return 1

    if not isinstance(events, list):
        print("ERROR: events.json must contain a top-level JSON array.")
        return 1

    cleaned_events, messages = inspect_events(events)

    print("Orphan cleanup report")
    print("=" * 72)

    if messages:
        for message in messages:
            print(message)
    else:
        print("No orphaned local gallery references were found.")

    removed_count = sum(message.startswith("[REMOVE]") for message in messages)
    print("-" * 72)
    print(f"Entries marked for removal: {removed_count}")

    if not args.apply:
        print("\nDry run only. No files were changed.")
        print("Run this to apply the cleanup:")
        print("    python cleanup_orphaned_gallery.py --apply")
        return 0

    if removed_count == 0:
        print("\nNothing to change.")
        return 0

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = EVENTS_PATH.with_name(f"events.backup-{timestamp}.json")

    try:
        shutil.copy2(EVENTS_PATH, backup_path)
        EVENTS_PATH.write_text(
            json.dumps(cleaned_events, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        print(f"ERROR: Could not write cleanup: {error}")
        return 1

    print(f"\nBackup created: {backup_path}")
    print(f"Cleaned file written: {EVENTS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
