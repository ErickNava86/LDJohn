import os

from flask import Flask, render_template, url_for, Response

from config import Config
from .admin import admin
from .cloudinary_manager import (
    configure_cloudinary,
    download_events_data,
    download_lessons_data,
    download_home_data,
)
from .data_manager import (
    get_all_events,
    get_cruise_flyers,
    get_event,
    get_homepage_gallery,
    get_local_flyers,
    load_home,
    load_lessons,
    replace_local_events,
    replace_local_home,
    replace_local_lessons,
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

    remote_events = download_events_data()
    if remote_events is not None:
        replace_local_events(remote_events)

    remote_lessons = download_lessons_data()
    if remote_lessons is not None:
        replace_local_lessons(remote_lessons)

    remote_home = download_home_data()
    if remote_home is not None:
        replace_local_home(remote_home)

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
        home_sections=load_home(),
        local_flyers=get_local_flyers(),
        cruise_flyers=get_cruise_flyers(),
        homepage_gallery=get_homepage_gallery(),
        seo_title="Line Dancing John | Lessons, Events & Private Bookings",
        seo_description=(
            "Line Dancing John offers fun and welcoming line dancing lessons, "
            "events, private instruction, parties, business events, and cruise "
            "ship classes in Southern California."
        ),
    )

    @app.route("/gallery")
    def gallery():
        return render_template(
        "gallery.html",
        events=get_all_events(),
        seo_title="Line Dancing Events & Photo Gallery | Line Dancing John",
        seo_description=(
            "Explore Line Dancing John's events and photo galleries from "
            "line dancing classes, parties, pop-ups, cruises, and special events."
        ),
    )

    @app.route("/gallery/<slug>")
    def event_page(slug):
        event = get_event(slug)

        return render_template(
        "event.html",
        event=event,
        seo_title=f"{event['title']} | Line Dancing John",
        seo_description=(
            f"View photos and details from {event['title']} "
            f"at {event['venue']} with Line Dancing John."
        ),
    )

    @app.route("/lessons")
    def lessons():
        return render_template(
        "lessons.html",
        lessons=load_lessons(),
        seo_title="Line Dancing Lessons | Line Dancing John",
        seo_description=(
            "Find current line dancing lessons and dances taught by Line Dancing John, "
            "with welcoming instruction for beginners and experienced dancers."
        ),
    )

    @app.route("/sitemap.xml")
    def sitemap():
        pages = [
        url_for("home", _external=True),
        url_for("lessons", _external=True),
        url_for("gallery", _external=True),
            ]

        for event in get_all_events():
            pages.append(
                url_for(
                    "event_page",
                    slug=event["slug"],
                    _external=True
                )
            )

        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        )

        for page in pages:
            xml.append("<url>")
            xml.append(f"<loc>{page}</loc>")
            xml.append("</url>")

        xml.append("</urlset>")

        return Response(
            "\n".join(xml),
            mimetype="application/xml"
        )

    @app.route("/robots.txt")
    def robots():
        content = """User-agent: *
                Allow: /
            Disallow: /admin/
    
        Sitemap: https://ldjohn.com/sitemap.xml
        """
    
        return Response(
            content,
            mimetype="text/plain"
        )

    return app
