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
    add_home_section,
    delete_home_image,
    delete_home_section,
    get_home_section,
    load_home,
    move_home_image,
    move_home_section,
    update_home_section,
    add_lesson,
    delete_lesson,
    load_lessons,
    move_lesson,
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

    existing = {
        event["slug"]
        for event in load_events()
    }

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


# ---------- LOGIN / LOGOUT ----------

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

    return render_template(
        "admin/login.html",
        error=error,
    )


@admin.route("/admin/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()

    return redirect(url_for("admin.login"))


# ---------- MAIN ADMIN DASHBOARD ----------

@admin.route("/admin")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")


# ---------- EVENTS DASHBOARD ----------

@admin.route("/admin/events")
@admin_required
def events_dashboard():
    return render_template(
        "admin/events.html",
        events=load_events(),
    )


# ---------- ADD EVENT ----------

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

        return redirect(
            url_for("admin.events_dashboard")
        )

    return render_template("admin/add_event.html")


# ---------- EDIT EVENT ----------

@admin.route("/admin/edit/<slug>", methods=["GET", "POST"])
@admin_required
def edit_event_page(slug):
    event = get_event_record(slug)

    if event is None:
        return redirect(
            url_for("admin.events_dashboard")
        )

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

        image_number = next_gallery_number(
            event["gallery"]
        )

        for photo in request.files.getlist("photos"):
            if not photo or not photo.filename:
                continue

            uploaded = upload_image(
                photo,
                f"ldjohn/events/{slug}/{image_number}",
            )

            uploaded["caption"] = ""
            event["gallery"].append(uploaded)

            image_number = next_gallery_number(
                event["gallery"]
            )

        update_event(slug, event)

        return redirect(
            url_for("admin.events_dashboard")
        )

    return render_template(
        "admin/edit_event.html",
        event=get_event(slug),
    )


# ---------- EVENT PHOTOS ----------

@admin.route("/admin/photos/<slug>")
@admin_required
def photos_page(slug):
    event = get_event(slug)

    if event is None:
        return redirect(
            url_for("admin.events_dashboard")
        )

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
        return redirect(
            url_for("admin.events_dashboard")
        )

    event["gallery"] = [
        photo
        for photo in event.get("gallery", [])
        if photo.get("public_id") != public_id
    ]

    update_event(slug, event)
    delete_image(public_id)

    return redirect(
        url_for(
            "admin.photos_page",
            slug=slug,
        )
    )


# ---------- DELETE EVENT ----------

@admin.route("/admin/delete/<slug>", methods=["POST"])
@admin_required
def delete_event_page(slug):
    event = get_event_record(slug)

    delete_event(slug)

    if event:
        cover = event.get("cover") or {}

        delete_image(
            cover.get("public_id")
        )

        for photo in event.get("gallery", []):
            delete_image(
                photo.get("public_id")
            )

    return redirect(
        url_for("admin.events_dashboard")
    )


# ---------- HOME MANAGEMENT ----------

@admin.route("/admin/home")
@admin_required
def home_page():
    return render_template(
        "admin/home.html",
        sections=load_home(),
    )


@admin.route("/admin/home/section/add", methods=["POST"])
@admin_required
def add_home_section_page():
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("admin.home_page"))

    base_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"
    existing = {section.get("id") for section in load_home()}
    section_id = base_id
    count = 2
    while section_id in existing:
        section_id = f"{base_id}-{count}"
        count += 1

    add_home_section({
        "id": section_id,
        "title": title,
        "type": "manual",
        "images": [],
    })
    return redirect(url_for("admin.home_page"))


@admin.route("/admin/home/section/<section_id>/rename", methods=["POST"])
@admin_required
def rename_home_section_page(section_id):
    section = get_home_section(section_id)
    if section is not None:
        title = request.form.get("title", "").strip()
        if title:
            section["title"] = title
            update_home_section(section_id, section)
    return redirect(url_for("admin.home_page"))


@admin.route("/admin/home/section/<section_id>/move", methods=["POST"])
@admin_required
def move_home_section_page(section_id):
    move_home_section(section_id, request.form.get("direction", ""))
    return redirect(url_for("admin.home_page"))


@admin.route("/admin/home/section/<section_id>/delete", methods=["POST"])
@admin_required
def delete_home_section_page(section_id):
    removed = delete_home_section(section_id)

    if removed:
        for image in removed.get("images", []):
            delete_image(image.get("public_id"))

    return redirect(url_for("admin.home_page"))


@admin.route("/admin/home/section/<section_id>/images", methods=["POST"])
@admin_required
def upload_home_images_page(section_id):
    section = get_home_section(section_id)
    if section is None or section.get("type") != "manual":
        return redirect(url_for("admin.home_page"))

    images = section.setdefault("images", [])
    used_numbers = set()
    for image in images:
        final_part = image.get("public_id", "").rsplit("/", 1)[-1]
        if final_part.isdigit():
            used_numbers.add(int(final_part))

    image_number = 1
    for photo in request.files.getlist("home_photos"):
        if not photo or not photo.filename:
            continue
        while image_number in used_numbers:
            image_number += 1
        uploaded = upload_image(
            photo,
            f"ldjohn/home/{section_id}/{image_number}",
        )
        images.append(uploaded)
        used_numbers.add(image_number)
        image_number += 1

    update_home_section(section_id, section)
    return redirect(url_for("admin.home_page"))


@admin.route("/admin/home/image/delete", methods=["POST"])
@admin_required
def delete_home_image_page():
    section_id = request.form["section_id"]
    public_id = request.form["public_id"]
    delete_home_image(section_id, public_id)
    delete_image(public_id)
    return redirect(url_for("admin.home_page"))


@admin.route("/admin/home/image/move", methods=["POST"])
@admin_required
def move_home_image_page():
    move_home_image(
        request.form["section_id"],
        request.form["public_id"],
        request.form["direction"],
    )
    return redirect(url_for("admin.home_page"))


# ---------- LESSONS ----------

@admin.route("/admin/lessons", methods=["GET", "POST"])
@admin_required
def lessons_page():
    if request.method == "POST":
        lesson_files = request.files.getlist(
            "lesson_photos"
        )

        lessons = load_lessons()
        image_number = len(lessons) + 1

        for photo in lesson_files:
            if not photo or not photo.filename:
                continue

            uploaded = upload_image(
                photo,
                f"ldjohn/lessons/{image_number}",
            )

            add_lesson(uploaded)

            image_number += 1

        return redirect(
            url_for("admin.lessons_page")
        )

    return render_template(
        "admin/lessons.html",
        lessons=load_lessons(),
    )


@admin.route("/admin/lessons/delete", methods=["POST"])
@admin_required
def delete_lesson_page():
    public_id = request.form["public_id"]

    delete_lesson(public_id)
    delete_image(public_id)

    return redirect(
        url_for("admin.lessons_page")
    )


@admin.route("/admin/lessons/move", methods=["POST"])
@admin_required
def move_lesson_page():
    public_id = request.form["public_id"]
    direction = request.form["direction"]

    move_lesson(
        public_id,
        direction,
    )

    return redirect(
        url_for("admin.lessons_page")
    )