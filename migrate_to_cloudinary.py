"""Safely standardize legacy event media into Cloudinary format."""

import os
import sys

from app import create_app
from app.cloudinary_manager import upload_image
from app.data_manager import load_events, save_events

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

DRY_RUN = "--apply" not in sys.argv

app = create_app()


def local_images(folder):
    if not os.path.isdir(folder):
        return []

    return sorted(
        filename
        for filename in os.listdir(folder)
        if filename.lower().endswith(VALID_EXTENSIONS)
        and not filename.startswith(".")
    )


def is_cloudinary_photo(photo):
    return (
        isinstance(photo, dict)
        and photo.get("url", "").startswith("https://res.cloudinary.com/")
        and photo.get("public_id")
    )


def find_local_file(folder, image_name):
    for extension in VALID_EXTENSIONS:
        filename = f"{image_name}{extension}"
        path = os.path.join(folder, filename)

        if os.path.exists(path):
            return path

    return None


with app.app_context():

    events = load_events()

    print()
    print("LDJ-022 DATA STANDARDIZATION")
    print("=" * 60)

    if DRY_RUN:
        print("DRY RUN — nothing will be uploaded or changed.")
    else:
        print("APPLY MODE — Cloudinary and events.json WILL be updated.")

    print()

    for event in events:

        slug = event["slug"]

        folder = os.path.join(
            "app",
            "static",
            "images",
            "events",
            slug,
        )

        print(f"EVENT: {slug}")

        # ---------------------------------
        # COVER
        # ---------------------------------

        cover = event.get("cover")

        if (
            isinstance(cover, dict)
            and cover.get("url")
            and cover.get("public_id")
        ):
            print("  COVER: already standardized")

        else:

            cover_path = None

            for extension in VALID_EXTENSIONS:
                candidate = os.path.join(
                    folder,
                    f"cover{extension}",
                )

                if os.path.exists(candidate):
                    cover_path = candidate
                    break

            if cover_path:

                print(
                    f"  COVER: migrate {cover_path}"
                )

                if not DRY_RUN:
                    event["cover"] = upload_image(
                        cover_path,
                        f"ldjohn/events/{slug}/cover",
                    )

            else:
                print("  COVER: no local cover found")

        # ---------------------------------
        # GALLERY
        # ---------------------------------

        gallery = event.get("gallery", [])

        standardized_gallery = []

        existing_public_ids = set()

        # Keep existing Cloudinary records.
        for photo in gallery:

            if is_cloudinary_photo(photo):

                standardized = {
                    "url": photo["url"],
                    "public_id": photo["public_id"],
                    "caption": photo.get("caption", ""),
                }

                standardized_gallery.append(
                    standardized
                )

                existing_public_ids.add(
                    photo["public_id"]
                )

                print(
                    f"  KEEP: {photo['public_id']}"
                )

        # Handle legacy records.
        for photo in gallery:

            if is_cloudinary_photo(photo):
                continue

            image_name = None
            caption = ""

            # Old schema:
            # {"image": "1", "caption": ""}
            if isinstance(photo, dict) and photo.get("image"):

                image_name = str(
                    photo["image"]
                )

                caption = photo.get(
                    "caption",
                    "",
                )

            # Transitional schema:
            # {"url": "images/events/.../1.jpg"}
            elif isinstance(photo, dict) and photo.get("url"):

                local_url = photo["url"]

                if local_url.startswith(
                    "images/events/"
                ):

                    filename = os.path.basename(
                        local_url
                    )

                    image_name = os.path.splitext(
                        filename
                    )[0]

                    caption = photo.get(
                        "caption",
                        "",
                    )

            if not image_name:
                print(
                    f"  SKIP UNKNOWN RECORD: {photo}"
                )
                continue

            public_id = (
                f"ldjohn/events/{slug}/{image_name}"
            )

            # Prevent duplicate Cloudinary objects.
            if public_id in existing_public_ids:

                print(
                    f"  DUPLICATE SKIPPED: {public_id}"
                )
                continue

            local_path = find_local_file(
                folder,
                image_name,
            )

            if not local_path:

                print(
                    f"  MISSING LOCAL IMAGE: {image_name}"
                )
                continue

            print(
                f"  MIGRATE: {local_path}"
                f" -> {public_id}"
            )

            if not DRY_RUN:

                uploaded = upload_image(
                    local_path,
                    public_id,
                )

                uploaded["caption"] = caption

                standardized_gallery.append(
                    uploaded
                )

                existing_public_ids.add(
                    public_id
                )

        if not DRY_RUN:
            event["gallery"] = standardized_gallery

        print()

    if DRY_RUN:

        print("=" * 60)
        print("DRY RUN COMPLETE.")
        print("No files or Cloudinary assets were changed.")
        print()
        print(
            "If the report looks correct, run:"
        )
        print(
            "python migrate_to_cloudinary.py --apply"
        )

    else:

        save_events(events)

        print("=" * 60)
        print("LDJ-022 STANDARDIZATION COMPLETE.")