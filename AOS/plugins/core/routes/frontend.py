# pyxfluff 2024-2025

from AOS import globals
from AOS.plugins.database import db

from time import time
from pathlib import Path

from fastapi import Request
from fastapi.responses import PlainTextResponse

if globals.is_dev:
    from .utils.reports.report import daily_report
else:
    def daily_report(db):
        print("[x] Request to spawn daily report ignored due to missing modules")


root = Path(__file__).parents[1]
day = 0


class Frontend():
    def __init__(self, app):
        self.app = app
        self.t = time()

    def initialize_frontend(self):
        @self.app.get("/")
        async def index(req: Request):
            global day

            if day != round(time() / 86400):
                day = round(time() / 86400)
                (globals.is_dev) and print(
                    "Ignoring reporting request, this will go through on prod"
                ) or daily_report(db)

            return PlainTextResponse(
                f"This is an Administer AOS instance. All routes are under /pub and /api.\n\nDocs: /docs#\nVersion: {globals.version}")

        @self.app.get("/app/{app:str}")
        def app_frontend(req: Request, app: str):
            pass
