from flask import Flask
import csv
import io
import datetime

from flask_migrate import Migrate

from rki_wrap.update import run_update, show
from rki_wrap.model import db, Entry
from rki_wrap import config


def create_app():
    app = Flask(__name__)
    app.config.from_object("rki_wrap.config")

    db.init_app(app)
    Migrate(app, db)

    @app.route("/")
    def home():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["date", "location", "incidence_7d"])
        writer.writeheader()
        for entry in Entry.query.filter(
            Entry.date > datetime.date.today() - config.DATE_WINDOW
        ).all():
            writer.writerow(
                {
                    "date": entry.date,
                    "location": entry.loc,
                    "incidence_7d": entry.inc_7d,
                }
            )

        return buf.getvalue()

    app.cli.command("update")(run_update)
    app.cli.command("show")(show)

    return app
