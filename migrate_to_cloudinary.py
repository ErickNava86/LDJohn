"""One-time migration of existing local event images into Cloudinary."""

import os

from app import create_app
from app.cloudinary_manager import upload_image
from app.data_manager import load_events, save_events

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

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


with app.app_context():
    events = load_events()

    for event in events:
        slug = event["slug"]
        folder = os.path.join("app", "static", "images", "events", slug)
        files = local_images(folder)

        cover_file = next(
            (filename for filename in files if filename.startswith("cover")),
            None,
        )

        if cover_file:
            event["cover"] = upload_image(
                os.path.join(folder, cover_file),
                f"ldjohn/events/{slug}/cover",
            )
        else:
            event.setdefault("cover", None)

        gallery = []
        image_number = 1

        for filename in files:
            if filename.startswith("cover"):
                continue

            uploaded = upload_image(
                os.path.join(folder, filename),
                f"ldjohn/events/{slug}/{image_number}",
            )
            uploaded["caption"] = ""
            gallery.append(uploaded)
            image_number += 1

        event["gallery"] = gallery
        print(f"{slug}: uploaded {len(gallery)} gallery photos")

    save_events(events)
    print("Migration complete.")
