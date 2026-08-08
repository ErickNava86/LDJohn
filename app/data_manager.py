import json
import os
import random
from copy import deepcopy
from typing import Any

from .cloudinary_manager import (
    upload_events_data,
    upload_lessons_data,
)

EVENTS_FILE = "data/events.json"
LESSONS_FILE = "data/lessons.json"

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

# ---------- LESSONS ----------

def load_lessons() -> list[dict[str, Any]]:
    with open(LESSONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_lessons(lessons: list[dict[str, Any]]) -> None:
    upload_lessons_data(lessons)

    with open(LESSONS_FILE, "w", encoding="utf-8") as file:
        json.dump(lessons, file, indent=4)

def replace_local_lessons(lessons: list[dict[str, Any]]) -> None:
    """Write lesson metadata locally without uploading it again during startup sync."""
    with open(LESSONS_FILE, "w", encoding="utf-8") as file:
        json.dump(lessons, file, indent=4)


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


# ---------- LESSON CRUD ----------

def add_lesson(lesson: dict[str, Any]) -> None:
    lessons = load_lessons()
    lessons.append(lesson)
    save_lessons(lessons)


def delete_lesson(public_id: str) -> None:
    lessons = load_lessons()

    remaining = [
        lesson
        for lesson in lessons
        if lesson.get("public_id") != public_id
    ]

    save_lessons(remaining)


def move_lesson(public_id: str, direction: str) -> None:
    lessons = load_lessons()

    index = next(
        (
            i
            for i, lesson in enumerate(lessons)
            if lesson.get("public_id") == public_id
        ),
        None,
    )

    if index is None:
        return

    if direction == "up" and index > 0:
        lessons[index - 1], lessons[index] = lessons[index], lessons[index - 1]

    elif direction == "down" and index < len(lessons) - 1:
        lessons[index + 1], lessons[index] = lessons[index], lessons[index + 1]

    save_lessons(lessons)