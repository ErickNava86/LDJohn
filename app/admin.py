from functools import wraps
import hmac
import os
import re
import shutil

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.utils import secure_filename

from .data_manager import (
    add_event,
    delete_event,
    get_all_events,
    get_event,
    load_events,
    update_event
)

admin = Blueprint("admin", __name__)


def admin_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))

        return view_function(*args, **kwargs)

    return wrapped_view


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


@admin.route("/admin/login", methods=["GET", "POST"])
def login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        username_matches = hmac.compare_digest(
            username,
            current_app.config["ADMIN_USERNAME"]
        )
        password_matches = hmac.compare_digest(
            password,
            current_app.config["ADMIN_PASSWORD"]
        )

        if username_matches and password_matches:
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))

        error = "Invalid username or password."

    return render_template(
        "admin/login.html",
        error=error
    )


@admin.route("/admin/logout", methods=["POST"])
@admin_required
def logout():

    session.clear()
    return redirect(url_for("admin.login"))


@admin.route("/admin")
@admin_required
def dashboard():

    events = get_all_events()

    return render_template(
        "admin/dashboard.html",
        events=events
    )


@admin.route("/admin/add", methods=["GET", "POST"])
@admin_required
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

        add_event(new_event)

        event_folder = os.path.join(
            "app",
            "static",
            "images",
            "events",
            slug
        )

        os.makedirs(event_folder, exist_ok=True)

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
@admin_required
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

        event_folder = os.path.join(
            "app",
            "static",
            "images",
            "events",
            slug
        )

        os.makedirs(event_folder, exist_ok=True)

        cover = request.files.get("cover_photo")

        if cover and cover.filename:

            for file in os.listdir(event_folder):

                if file.startswith("cover"):
                    os.remove(os.path.join(event_folder, file))

            filename = secure_filename(cover.filename)
            extension = os.path.splitext(filename)[1]

            cover.save(
                os.path.join(
                    event_folder,
                    f"cover{extension}"
                )
            )

        gallery = request.files.getlist("photos")

        if gallery:

            image_number = 1

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


@admin.route("/admin/photos/<slug>")
@admin_required
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

            photos.append(f"images/events/{slug}/{file}")

    return render_template(
        "admin/photos.html",
        event=event,
        photos=photos
    )


@admin.route("/admin/delete-photo", methods=["POST"])
@admin_required
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
@admin_required
def delete_event_page(slug):

    delete_event(slug)

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
