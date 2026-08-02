import json
import os
import random

# ---------- EVENTS ----------

def load_events():
    with open("data/events.json", "r") as file:
        return json.load(file)


def save_events(events):
    with open("data/events.json", "w") as file:
        json.dump(events, file, indent=4)


# ---------- IMAGE HELPERS ----------

def get_images(folder):
    """
    Returns a sorted list of image filenames in a folder.
    """

    valid_extensions = (".png", ".jpg", ".jpeg", ".webp")

    return sorted(
        file
        for file in os.listdir(folder)
        if file.lower().endswith(valid_extensions)
        and not file.startswith(".")
    )

def find_image(slug, image_name):
    """
    Finds an image regardless of file extension.
    """

    folder = f"app/static/images/events/{slug}"

    valid_extensions = (".png", ".jpg", ".jpeg", ".webp")

    for extension in valid_extensions:

        filename = image_name + extension

        if os.path.exists(os.path.join(folder, filename)):
            return filename

    return None


def get_local_flyers():
    return get_images("app/static/images/flyers/local")


def get_cruise_flyers():
    return get_images("app/static/images/flyers/cruise")


def image_path(slug, filename):
    return f"images/events/{slug}/{filename}"


def prepare_event(event):

    event = event.copy()

    cover = find_image(
        event["slug"],
        "cover"
    )

    if cover:
        event["cover_url"] = image_path(
            event["slug"],
            cover
        )
    else:
        event["cover_url"] = None

    event["gallery"] = discover_gallery_images(
        event["slug"]
    )

    return event

# -------- MAIN GALLERY HELPERS -----------

def discover_gallery_images(slug):

    folder = f"app/static/images/events/{slug}"

    gallery = []

    valid_extensions = (".png", ".jpg", ".jpeg", ".webp")

    for file in os.listdir(folder):

        if file.startswith("."):
            continue

        if file.startswith("cover"):
            continue

        if not file.lower().endswith(valid_extensions):
            continue

        gallery.append({
            "url": image_path(slug, file),
            "caption": ""
        })

    gallery.sort(key=lambda image: image["url"])

    return gallery


def get_all_gallery_images():

    photos = []

    events = load_events()

    for event in events:
        photos.extend(
            discover_gallery_images(event["slug"])
        )

    return photos


def get_homepage_gallery(count=9):

    photos = get_all_gallery_images()

    random.shuffle(photos)

    return photos[:count]

# ---------- CRUD ----------

def get_all_events():

    events = load_events()

    return [prepare_event(event) for event in events]


def get_event(slug):

    events = load_events()

    for event in events:
        if event["slug"] == slug:
            return prepare_event(event)

    return None


def add_event(new_event):

    events = load_events()

    events.append(new_event)

    save_events(events)


def update_event(slug, updated_event):

    events = load_events()

    for i, event in enumerate(events):

        if event["slug"] == slug:

            events[i] = updated_event

            save_events(events)

            return


def delete_event(slug):

    events = load_events()

    for i, event in enumerate(events):

        if event["slug"] == slug:

            del events[i]

            save_events(events)

            return
        


