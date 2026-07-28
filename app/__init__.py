from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():

        flyers = [
            "flyer1.png",
            "flyer2.png",
            "flyer-chaparral.jpg",
            "flyer-vfw.png"
        ]

        cruise_flyers = [
            "flyer-easter.png",
            "flyer-royal.png"
        ]

        gallery = [
            "image1.png",
            "image2.png",
            "image3.jpg",
            "image4.png",
            "image5.jpg",
            "image6.jpg",
            "image7.jpg",
            "image8.jpg",
            "image9.jpg",
            "image10.jpg",
            "image11.jpg",
            "image12.jpg",
        ]

        from flask import render_template
        return render_template("index.html", flyers=flyers, cruise_flyers=cruise_flyers, gallery = gallery)

    return app