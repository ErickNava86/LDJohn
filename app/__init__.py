from flask import Flask, render_template

from .admin import admin
from .data_manager import (
    get_all_events,
    get_event,
    get_local_flyers,
    get_cruise_flyers,
    get_homepage_gallery
)


# ---------- APP ----------

def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "super-secret-key-change-me"
    app.config["ADMIN_PASSWORD"] = "dance2026"

    app.register_blueprint(admin)

    @app.route("/")
    def home():

        return render_template(
            "index.html",
            events=get_all_events(),
            local_flyers=get_local_flyers(),
            cruise_flyers=get_cruise_flyers(),
            homepage_gallery=get_homepage_gallery()
        )


    @app.route("/gallery")
    def gallery():

        return render_template(
            "gallery.html",
            events=get_all_events()
        )


    @app.route("/gallery/<slug>")
    def event_page(slug):

        return render_template(
            "event.html",
            event=get_event(slug)
        )


    return app