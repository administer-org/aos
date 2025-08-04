# pyxfluff 2025

import sass

from time import time

from fastapi import APIRouter, Request
from fastapi.responses import (
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pathlib import Path

from AOS.plugins.database import get_web_database
from AOS import il

db = get_web_database()

class AdminFrontend:
    def __init__(self, app):
        self.app = app
        self.startup_time = time()
        self.router = APIRouter()
        self.templates = Jinja2Templates(
            (Path(__file__).parent / "../templates").resolve()
        )

    def mount(self):
        # mount static content
        self.app.mount(
            "/a/static",
            StaticFiles(directory=(Path(__file__).parent / "../static").resolve()),
            name="static",
        )

        # compile css
        (Path(__file__).parent / "../static/css").resolve().mkdir(
            parents=True, exist_ok=True
        )

        for scss in (Path(__file__).parent / "../static/scss").resolve().glob("*.scss"):
            css_file = (Path(__file__).parent / "../static/css").resolve() / (
                scss.stem + ".css"
            )
            try:
                css_file.write_text(sass.compile(filename=str(scss)))
                il.cprint(f"[✓] Compiled {scss.name} → {css_file.name}", 32)
            except Exception as e:
                il.cprint(f"[x] Failed to compile {scss.name}: {e}", 32)

        @self.router.get("/")
        def root(req: Request):
            aos_auth = req.cookies.get("AOS_-SessionAuth")

            if aos_auth is None:
                return RedirectResponse("/a/login?type=logged_out")
            else:
                # verify token
                token_data = db.get(aos_auth, db.SESSIONS)

                if token_data is None:
                    return RedirectResponse("/a/login?type=logged_out")
                elif token_data["expiry"] <= time():
                    db.delete(aos_auth, db.SESSIONS)
                    return RedirectResponse("/a/login?type=timeout")
                else:
                    return RedirectResponse("/a/home")

        @self.router.get("/login")
        def login_page(req: Request):
            return self.templates.TemplateResponse(
                "auth/login.html", context={"login_allowed": True, "request": req}
            )
        
        @self.router.get("/signup")
        def signup_page(req: Request):
            return self.templates.TemplateResponse(
                "auth/signup.html", context={"signup_allowed": True, "request": req}
            )
