import json
import os
import random
from copy import deepcopy
from typing import Any

from .cloudinary_manager import upload_events_data

EVENTS_FILE = "data/events.json"
VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


# ---------- EVENTS ----------

def load_events() -> list[dict[str, Any]]:
    with open(EVENTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_events(events: list[dict[str, Any]]) -> None:
    # Persist remotely first. If this fails, the admin request fails instead of
    # pretending a temporary Render-only change was safely stored.
    upload_events_data(events)

    with open(EVENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)


def replace_local_events(events: list[dict[str, Any]]) -> None:
    """Write metadata locally without uploading it again during startup sync."""
    with open(EVENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)


# ---------- STATIC IMAGE HELPERS ----------

def get_images(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        return []

    return sorted(
        filename
        for filename in os.listdir(folder)
        if filename.lower().endswith(VALID_EXTENSIONS)
        and not filename.startswith(".")
    )


def get_local_flyers() -> list[str]:
    return get_images("app/static/images/flyers/local")


def get_cruise_flyers() -> list[str]:
    return get_images("app/static/images/flyers/cruise")

# ---------- EVENT PRESENTATION ----------

def normalize_gallery(event: dict[str, Any]) -> list[dict[str, str]]:
    gallery = []

    for photo in event.get("gallery", []):
        if not isinstance(photo, dict) or not photo.get("url"):
            continue

        gallery.append({
            "url": photo["url"],
            "public_id": photo.get("public_id", ""),
            "caption": photo.get("caption", ""),
        })

    return gallery


def prepare_event(event: dict[str, Any]) -> dict[str, Any]:
    prepared = deepcopy(event)

    cover = prepared.get("cover", {})
    prepared["cover_url"] = cover.get("url")

    prepared["gallery"] = normalize_gallery(prepared)
    return prepared


def get_all_gallery_images() -> list[dict[str, str]]:
    photos = []

    for event in get_all_events():
        photos.extend(event["gallery"])

    return photos


def get_homepage_gallery(count: int = 9) -> list[dict[str, str]]:
    photos = get_all_gallery_images()
    random.shuffle(photos)
    return photos[:count]


# ---------- CRUD ----------

def get_all_events() -> list[dict[str, Any]]:
    return [prepare_event(event) for event in load_events()]


def get_event(slug: str) -> dict[str, Any] | None:
    for event in load_events():
        if event["slug"] == slug:
            return prepare_event(event)

    return None


def get_event_record(slug: str) -> dict[str, Any] | None:
    for event in load_events():
        if event["slug"] == slug:
            return deepcopy(event)

    return None


def add_event(new_event: dict[str, Any]) -> None:
    events = load_events()
    events.append(new_event)
    save_events(events)


def update_event(slug: str, updated_event: dict[str, Any]) -> None:
    events = load_events()

    for index, event in enumerate(events):
        if event["slug"] == slug:
            events[index] = updated_event
            save_events(events)
            return


def delete_event(slug: str) -> None:
    events = load_events()
    remaining = [event for event in events if event["slug"] != slug]
    save_events(remaining)
