from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import shutil
import os
import re

from .data_manager import (
    load_events,
    add_event,
    get_all_events,
    get_event,
    update_event,
    delete_event
)

admin = Blueprint("admin", __name__)


def create_slug(title):

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    events = load_events()
    existing = {event["slug"] for event in events}

    original = slug
    count = 2

    while slug in existing:
        slug = f"{original}-{count}"
        count += 1

    return slug


@admin.route("/admin")
def dashboard():

    events = get_all_events()

    return render_template(
        "admin/dashboard.html",
        events=events
    )


@admin.route("/admin/add", methods=["GET", "POST"])
def add_event_page():

    if request.method == "POST":

        slug = create_slug(request.form["title"])

        new_event = {

            "title": request.form["title"],
            "slug": slug,
            "date": request.form["date"],
            "venue": request.form["venue"],
            "description": request.form["description"],
            "gallery": []

        }

        # Save event to JSON
        add_event(new_event)

        # Create image folder
        event_folder = os.path.join(
            "app",
            "static",
            "images",
            "events",
            slug
        )

        os.makedirs(event_folder, exist_ok=True)

        # Save cover image
        cover = request.files.get("cover_photo")

        if cover and cover.filename:

            filename = secure_filename(cover.filename)
            extension = os.path.splitext(filename)[1]

            cover.save(
                os.path.join(
                    event_folder,
                    f"cover{extension}"
                )
            )

        # Save gallery images
        gallery = request.files.getlist("gallery_photos")

        image_number = 1

        for photo in gallery:

            if photo and photo.filename:

                filename = secure_filename(photo.filename)
                extension = os.path.splitext(filename)[1]

                photo.save(
                    os.path.join(
                        event_folder,
                        f"{image_number}{extension}"
                    )
                )

                image_number += 1

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_event.html")


@admin.route("/admin/edit/<slug>", methods=["GET", "POST"])
def edit_event_page(slug):

    event = get_event(slug)

    if request.method == "POST":

        updated_event = {

            "title": request.form["title"],
            "slug": event["slug"],
            "date": request.form["date"],
            "venue": request.form["venue"],
            "description": request.form["description"],
            "gallery": event["gallery"]

        }

        update_event(slug, updated_event)

        # Replace cover photo

        cover = request.files.get("cover_photo")

        if cover and cover.filename:

            event_folder = os.path.join(
                "app",
                "static",
                "images",
                "events",
                slug
            )

            # Remove existing cover
            for file in os.listdir(event_folder):

                if file.startswith("cover"):

                    os.remove(
                        os.path.join(event_folder, file)
                    )

            filename = secure_filename(cover.filename)
            extension = os.path.splitext(filename)[1]

            cover.save(
                os.path.join(
                    event_folder,
                    f"cover{extension}"
                )
            )

            # ===========\
            # Upload new gallery photos

    gallery = request.files.getlist("photos")

    if gallery:

        event_folder = os.path.join(
            "app",
            "static",
            "images",
            "events",
            slug
        )

        image_number = 1

        # Find the next available image number
        while True:

            exists = False

            for file in os.listdir(event_folder):

                name = os.path.splitext(file)[0]

                if name == str(image_number):

                    exists = True
                    break

            if not exists:
                break

            image_number += 1

        # Save new images
        for photo in gallery:

            if photo and photo.filename:

                filename = secure_filename(photo.filename)
                extension = os.path.splitext(filename)[1]

                photo.save(
                    os.path.join(
                        event_folder,
                        f"{image_number}{extension}"
                    )
                )

                image_number += 1

        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/edit_event.html",
        event=event
    )


@admin.route("/admin/delete")
def delete_events_page():
    return render_template("admin/delete_events.html")


@admin.route("/admin/photos/<slug>")
def photos_page(slug):

    event = get_event(slug)

    event_folder = os.path.join(
        "app",
        "static",
        "images",
        "events",
        slug
    )

    photos = []

    if os.path.exists(event_folder):

        for file in sorted(os.listdir(event_folder)):

            if file.startswith("cover"):
                continue

            photos.append(
                f"images/events/{slug}/{file}"
            )

    return render_template(
        "admin/photos.html",
        event=event,
        photos=photos
    )

@admin.route("/admin/delete-photo", methods=["POST"])
def delete_photo():

    slug = request.form["slug"]
    photo = request.form["photo"]

    photo_path = os.path.join(
        "app",
        "static",
        photo
    )

    if os.path.exists(photo_path):
        os.remove(photo_path)

    return redirect(
        url_for(
            "admin.photos_page",
            slug=slug
        )
    )

@admin.route("/admin/delete/<slug>", methods=["POST"])
def delete_event_page(slug):

    # Remove event from events.json
    delete_event(slug)

    # Remove the event's image folder
    event_folder = os.path.join(
        "app",
        "static",
        "images",
        "events",
        slug
    )

    if os.path.exists(event_folder):
        shutil.rmtree(event_folder)

    return redirect(url_for("admin.dashboard"))