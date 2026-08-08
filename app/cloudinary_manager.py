import json
import os
import tempfile
from typing import Any

import cloudinary
import cloudinary.api
import cloudinary.uploader

EVENTS_DATA_PUBLIC_ID = "ldjohn/data/events.json"
LESSONS_DATA_PUBLIC_ID = "ldjohn/data/lessons.json"
HOME_DATA_PUBLIC_ID = "ldjohn/data/home.json"


def configure_cloudinary(config: dict[str, Any]) -> None:
    """Configure the Cloudinary SDK from Flask configuration."""
    cloudinary.config(
        cloud_name=config.get("CLOUDINARY_CLOUD_NAME"),
        api_key=config.get("CLOUDINARY_API_KEY"),
        api_secret=config.get("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def cloudinary_is_configured() -> bool:
    cfg = cloudinary.config()
    return bool(cfg.cloud_name and cfg.api_key and cfg.api_secret)


def upload_image(file_object, public_id: str) -> dict[str, str]:
    """Upload or replace an image and return the fields stored in events.json."""
    result = cloudinary.uploader.upload(
        file_object,
        public_id=public_id,
        overwrite=True,
        invalidate=True,
        resource_type="image",
    )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
    }


def delete_image(public_id: str | None) -> None:
    if not public_id:
        return

    cloudinary.uploader.destroy(
        public_id,
        resource_type="image",
        invalidate=True,
    )


def upload_events_data(events: list[dict[str, Any]]) -> None:
    """Persist event metadata as a private-to-the-app Cloudinary raw asset."""
    if not cloudinary_is_configured():
        return

    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(events, file, indent=4)

        cloudinary.uploader.upload(
            temp_path,
            public_id=EVENTS_DATA_PUBLIC_ID,
            resource_type="raw",
            overwrite=True,
            invalidate=True,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def upload_lessons_data(lessons: list[dict[str, Any]]) -> None:
    """Persist lesson metadata as a private-to-the-app Cloudinary raw asset."""
    if not cloudinary_is_configured():
        return

    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(lessons, file, indent=4)

        cloudinary.uploader.upload(
            temp_path,
            public_id=LESSONS_DATA_PUBLIC_ID,
            resource_type="raw",
            overwrite=True,
            invalidate=True,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def download_events_data() -> list[dict[str, Any]] | None:
    """Fetch the latest persisted event metadata, or None if none exists yet."""
    if not cloudinary_is_configured():
        return None

    try:
        resource = cloudinary.api.resource(
            EVENTS_DATA_PUBLIC_ID,
            resource_type="raw",
        )
        secure_url = resource["secure_url"]

        # Standard library only: no extra HTTP dependency is required.
        from urllib.request import urlopen

        with urlopen(secure_url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        # First deployment has no remote metadata yet; the bundled JSON remains the fallback.
        return None

def download_lessons_data() -> list[dict[str, Any]] | None:
    """Fetch the latest persisted lesson metadata, or None if none exists yet."""
    if not cloudinary_is_configured():
        return None

    try:
        resource = cloudinary.api.resource(
            LESSONS_DATA_PUBLIC_ID,
            resource_type="raw",
        )
        secure_url = resource["secure_url"]

        # Standard library only: no extra HTTP dependency is required.
        from urllib.request import urlopen

        with urlopen(secure_url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    except Exception:
        # First deployment has no remote lesson metadata yet;
        # the bundled lessons.json remains the fallback.
        return None

def upload_home_data(sections: list[dict[str, Any]]) -> None:
    """Persist homepage section metadata as a Cloudinary raw asset."""
    if not cloudinary_is_configured():
        return

    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(sections, file, indent=4)

        cloudinary.uploader.upload(
            temp_path,
            public_id=HOME_DATA_PUBLIC_ID,
            resource_type="raw",
            overwrite=True,
            invalidate=True,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def download_home_data() -> list[dict[str, Any]] | None:
    """Fetch the latest persisted homepage metadata, or None if none exists yet."""
    if not cloudinary_is_configured():
        return None

    try:
        resource = cloudinary.api.resource(
            HOME_DATA_PUBLIC_ID,
            resource_type="raw",
        )
        secure_url = resource["secure_url"]

        from urllib.request import urlopen

        with urlopen(secure_url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

