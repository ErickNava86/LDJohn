from functools import wraps
import hmac
import re

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .cloudinary_manager import delete_image, upload_image
from .data_manager import (
    add_event,
    delete_event,
    get_all_events,
    get_event,
    get_event_record,
    load_events,
    update_event,
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
    existing = {event["slug"] for event in load_events()}
    original = slug
    count = 2

    while slug in existing:
        slug = f"{original}-{count}"
        count += 1

    return slug


def next_gallery_number(gallery):
    used_numbers = set()

    for photo in gallery:
        public_id = photo.get("public_id", "")
        final_part = public_id.rsplit("/", 1)[-1]
        if final_part.isdigit():
            used_numbers.add(int(final_part))

    image_number = 1
    while image_number in used_numbers:
        image_number += 1

    return image_number


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
            current_app.config["ADMIN_USERNAME"],
        )
        password_matches = hmac.compare_digest(
            password,
            current_app.config["ADMIN_PASSWORD"],
        )

        if username_matches and password_matches:
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))

        error = "Invalid username or password."

    return render_template("admin/login.html", error=error)


@admin.route("/admin/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin.route("/admin")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        events=get_all_events(),
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
            "cover": None,
            "gallery": [],
        }

        cover = request.files.get("cover_photo")
        if cover and cover.filename:
            new_event["cover"] = upload_image(
                cover,
                f"ldjohn/events/{slug}/cover",
            )

        gallery_files = request.files.getlist("gallery_photos")
        image_number = 1

        for photo in gallery_files:
            if not photo or not photo.filename:
                continue

            uploaded = upload_image(
                photo,
                f"ldjohn/events/{slug}/{image_number}",
            )
            uploaded["caption"] = ""
            new_event["gallery"].append(uploaded)
            image_number += 1

        add_event(new_event)
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_event.html")


@admin.route("/admin/edit/<slug>", methods=["GET", "POST"])
@admin_required
def edit_event_page(slug):
    event = get_event_record(slug)

    if event is None:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        event["title"] = request.form["title"]
        event["date"] = request.form["date"]
        event["venue"] = request.form["venue"]
        event["description"] = request.form["description"]
        event.setdefault("gallery", [])

        cover = request.files.get("cover_photo")
        if cover and cover.filename:
            event["cover"] = upload_image(
                cover,
                f"ldjohn/events/{slug}/cover",
            )

        image_number = next_gallery_number(event["gallery"])

        for photo in request.files.getlist("photos"):
            if not photo or not photo.filename:
                continue

            uploaded = upload_image(
                photo,
                f"ldjohn/events/{slug}/{image_number}",
            )
            uploaded["caption"] = ""
            event["gallery"].append(uploaded)
            image_number = next_gallery_number(event["gallery"])

        update_event(slug, event)
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/edit_event.html",
        event=get_event(slug),
    )


@admin.route("/admin/photos/<slug>")
@admin_required
def photos_page(slug):
    event = get_event(slug)

    if event is None:
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/photos.html",
        event=event,
        photos=event["gallery"],
    )


@admin.route("/admin/delete-photo", methods=["POST"])
@admin_required
def delete_photo():
    slug = request.form["slug"]
    public_id = request.form["public_id"]
    event = get_event_record(slug)

    if event is None:
        return redirect(url_for("admin.dashboard"))

    event["gallery"] = [
        photo
        for photo in event.get("gallery", [])
        if photo.get("public_id") != public_id
    ]
    update_event(slug, event)
    delete_image(public_id)

    return redirect(url_for("admin.photos_page", slug=slug))


@admin.route("/admin/delete/<slug>", methods=["POST"])
@admin_required
def delete_event_page(slug):
    event = get_event_record(slug)

    delete_event(slug)

    if event:
        cover = event.get("cover") or {}
        delete_image(cover.get("public_id"))

        for photo in event.get("gallery", []):
            delete_image(photo.get("public_id"))

    return redirect(url_for("admin.dashboard"))
