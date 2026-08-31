import json
import os
import random
from copy import deepcopy
from typing import Any

from .cloudinary_manager import (
    upload_events_data,
    upload_lessons_data,
    upload_home_data,
)

EVENTS_FILE = "data/events.json"
LESSONS_FILE = "data/lessons.json"
HOME_FILE = "data/home.json"

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


# ---------- HOME ----------

def load_home() -> list[dict[str, Any]]:
    with open(HOME_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_home(sections: list[dict[str, Any]]) -> None:
    upload_home_data(sections)

    with open(HOME_FILE, "w", encoding="utf-8") as file:
        json.dump(sections, file, indent=4)


def replace_local_home(sections: list[dict[str, Any]]) -> None:
    """Write homepage metadata locally without uploading during startup sync."""
    with open(HOME_FILE, "w", encoding="utf-8") as file:
        json.dump(sections, file, indent=4)


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


def move_event(slug: str, direction: str) -> None:
    """Move an event up or down in the admin/public display order."""
    events = load_events()
    index = next(
        (i for i, event in enumerate(events) if event.get("slug") == slug),
        None,
    )

    if index is None:
        return

    if direction == "up" and index > 0:
        events[index - 1], events[index] = events[index], events[index - 1]
    elif direction == "down" and index < len(events) - 1:
        events[index + 1], events[index] = events[index], events[index + 1]
    else:
        return

    save_events(events)


# ---------- EVENT GALLERY MANAGEMENT ----------

def move_event_photo(slug: str, public_id: str, direction: str) -> None:
    event = get_event_record(slug)
    if event is None:
        return

    gallery = event.setdefault("gallery", [])
    index = next(
        (i for i, photo in enumerate(gallery) if photo.get("public_id") == public_id),
        None,
    )
    if index is None:
        return

    if direction == "up" and index > 0:
        gallery[index - 1], gallery[index] = gallery[index], gallery[index - 1]
    elif direction == "down" and index < len(gallery) - 1:
        gallery[index + 1], gallery[index] = gallery[index], gallery[index + 1]

    update_event(slug, event)


def update_event_photo_caption(slug: str, public_id: str, caption: str) -> None:
    event = get_event_record(slug)
    if event is None:
        return

    for photo in event.setdefault("gallery", []):
        if photo.get("public_id") == public_id:
            photo["caption"] = caption.strip()
            update_event(slug, event)
            return

# ---------- LESSON CRUD ----------

def add_lesson(lesson: dict[str, Any]) -> None:
    """Add a new lesson at the top so newest uploads display first."""
    lessons = load_lessons()
    lessons.insert(0, lesson)
    save_lessons(lessons)


def delete_lesson(lesson_url: str) -> str | None:
    """Delete exactly one lesson record, even if legacy public IDs are duplicated.

    Returns the Cloudinary public_id only when no remaining lesson record uses it.
    """
    lessons = load_lessons()
    index = next(
        (i for i, lesson in enumerate(lessons) if lesson.get("url") == lesson_url),
        None,
    )
    if index is None:
        return None

    removed = lessons.pop(index)
    public_id = removed.get("public_id")
    save_lessons(lessons)

    if public_id and not any(lesson.get("public_id") == public_id for lesson in lessons):
        return public_id
    return None


def move_lesson(lesson_url: str, direction: str) -> None:
    """Move the exact lesson selected by its unique stored URL.

    URL is used instead of public_id because older data contains duplicate
    Cloudinary public IDs created by the former len(lessons)+1 naming scheme.
    """
    lessons = load_lessons()
    index = next(
        (i for i, lesson in enumerate(lessons) if lesson.get("url") == lesson_url),
        None,
    )

    if index is None:
        return

    if direction == "up" and index > 0:
        lessons[index - 1], lessons[index] = lessons[index], lessons[index - 1]
    elif direction == "down" and index < len(lessons) - 1:
        lessons[index + 1], lessons[index] = lessons[index], lessons[index + 1]

    save_lessons(lessons)


# ---------- HOME CRUD ----------

def get_home_section(section_id: str) -> dict[str, Any] | None:
    for section in load_home():
        if section.get("id") == section_id:
            return deepcopy(section)
    return None


def add_home_section(section: dict[str, Any]) -> None:
    sections = load_home()
    sections.append(section)
    save_home(sections)


def update_home_section(section_id: str, updated_section: dict[str, Any]) -> None:
    sections = load_home()
    for index, section in enumerate(sections):
        if section.get("id") == section_id:
            sections[index] = updated_section
            save_home(sections)
            return


def delete_home_section(section_id: str) -> dict[str, Any] | None:
    sections = load_home()
    removed = None
    remaining = []

    for section in sections:
        if section.get("id") == section_id:
            removed = section
        else:
            remaining.append(section)

    if removed is not None:
        save_home(remaining)

    return removed


def move_home_section(section_id: str, direction: str) -> None:
    sections = load_home()
    index = next((i for i, section in enumerate(sections) if section.get("id") == section_id), None)

    if index is None:
        return

    if direction == "up" and index > 0:
        sections[index - 1], sections[index] = sections[index], sections[index - 1]
    elif direction == "down" and index < len(sections) - 1:
        sections[index + 1], sections[index] = sections[index], sections[index + 1]

    save_home(sections)


def move_home_image(section_id: str, public_id: str, direction: str) -> None:
    section = get_home_section(section_id)
    if section is None:
        return

    images = section.setdefault("images", [])
    index = next((i for i, image in enumerate(images) if image.get("public_id") == public_id), None)

    if index is None:
        return

    if direction == "up" and index > 0:
        images[index - 1], images[index] = images[index], images[index - 1]
    elif direction == "down" and index < len(images) - 1:
        images[index + 1], images[index] = images[index], images[index + 1]

    update_home_section(section_id, section)


def delete_home_image(section_id: str, public_id: str) -> None:
    section = get_home_section(section_id)
    if section is None:
        return

    section["images"] = [
        image for image in section.get("images", [])
        if image.get("public_id") != public_id
    ]
    update_home_section(section_id, section)

