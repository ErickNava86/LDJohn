import os

from flask import Flask, render_template, url_for

from config import Config
from .admin import admin
from .cloudinary_manager import (
    configure_cloudinary, 
    download_events_data, 
    download_lessons_data
    )

from .data_manager import (
    get_all_events,
    get_cruise_flyers,
    get_event,
    get_homepage_gallery,
    get_local_flyers,
    replace_local_events,
    replace_local_lessons,
    load_lessons
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    required_settings = (
        "SECRET_KEY",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
    )
    missing = [name for name in required_settings if not app.config.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    configure_cloudinary(app.config)

    # Restore John\'s latest event metadata before serving any page.
    remote_events = download_events_data()
    if remote_events is not None:
        replace_local_events(remote_events)

    # Restore John's latest lesson metadata before serving any page.
    remote_lessons = download_lessons_data()
    if remote_lessons is not None:
        replace_local_lessons(remote_lessons)

    app.register_blueprint(admin)

    def versioned_static(filename):
        file_path = os.path.join(app.static_folder, filename)

        try:
            version = int(os.path.getmtime(file_path))
        except OSError:
            version = 0

        return url_for("static", filename=filename, v=version)

    def image_src(value):
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        return versioned_static(value)

    app.jinja_env.globals["versioned_static"] = versioned_static
    app.jinja_env.globals["image_src"] = image_src

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            events=get_all_events(),
            local_flyers=get_local_flyers(),
            cruise_flyers=get_cruise_flyers(),
            homepage_gallery=get_homepage_gallery(),
        )

    @app.route("/gallery")
    def gallery():
        return render_template(
            "gallery.html",
            events=get_all_events(),
        )

    @app.route("/gallery/<slug>")
    def event_page(slug):
        return render_template(
            "event.html",
            event=get_event(slug),
        )

    @app.route("/lessons")
    def lessons():
        return render_template(
        "lessons.html",
        lessons=load_lessons(),
    )

    return app
