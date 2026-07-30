from flask import Blueprint, render_template, request, redirect, url_for
from .data_manager import load_events, add_event
import re

admin = Blueprint("admin", __name__)

from .data_manager import load_events
import re

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

    events = load_events()

    return render_template(
        "admin/dashboard.html",
        events=events
    )

@admin.route("/admin/add", methods=["GET", "POST"])
def add_event_page():

    if request.method == "POST":

        new_event = {

            "title": request.form["title"],
            "slug": create_slug(request.form["title"]),
            "date": request.form["date"],
            "venue": request.form["venue"],
            "description": request.form["description"],

            "cover_image": "john-love.png",
            "gallery": [],

        }

        add_event(new_event)

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_event.html")


@admin.route("/admin/edit")
def edit_events_page():
    return render_template("admin/edit_events.html")


@admin.route("/admin/delete")
def delete_events_page():
    return render_template("admin/delete_events.html")


@admin.route("/admin/upload")
def upload_page():
    return render_template("admin/upload.html")