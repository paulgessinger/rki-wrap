from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()


class Entry(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.Date())
    loc = db.Column(db.String(255))
    inc_7d = db.Column(db.Float())
