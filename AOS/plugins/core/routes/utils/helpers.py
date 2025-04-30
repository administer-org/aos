# pyxfluff 2024-2025

from AOS.plugins.database import db


def request_app(app_id):
    return db.get(app_id, db.APPS)


def upload_app(data):
    pass
