# pyxfluff 2025

import time
import bcrypt
import nanoid

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from AOS.plugins.database import get_web_database

db = get_web_database()


class AdminRoutes:
    def __init__(self, app):
        self.app = app
        self.startup_time = time.time()
        self.router = APIRouter()

    def mount_api(self):
        @self.router.get("/test")
        def test_admin():
            print("OK")

        @self.router.post("/login")
        async def generate_keys(req: Request, resp: Response):
            data = await req.json()
            user = db.get(data["username"], db.USERS)

            if user is None:
                return JSONResponse(
                    {"code": 401, "data": "Your account was not found."},
                    status_code=401
                )
            elif user["inactive"]:
                return JSONResponse(
                    {"code": 401, "data": "Your account has been deactivated."},
                    status_code=401
                )
            elif not bcrypt.checkpw(
                data["password"].encode(), user["password"].encode()
            ):
                return JSONResponse(
                    {"code": 401, "data": "Incorrect password."}, status_code=401
                )

            # create session
            session = {
                "id": nanoid.generate(),
                "creation": time.time(),
                "ip": req.headers.get("CF-Connecting-IP"),
                "browser": req.headers.get("User-Agent")
            }

            user["sessions"].append(f"{user["username"]}-{session["id"]}")

            db.set(data["username"], user, db.USERS)
            db.set(f"{user["username"]}-{session["id"]}", session, db.SESSIONS)

            resp.set_cookie(
                key="AOS_-SessionAuth",
                value=session["id"],
                max_age=data["stayLoggedIn"] and None or 86400,
                httponly=True,
                samesite="strict",
                secure=True
            )

            return JSONResponse(
                {"code": 200, "data": "Redirecting..."}, status_code=200
            )

        @self.router.post("/signup")
        async def signup(req: Request):
            data = await req.json()
            token = db.get(data["signup_token"], db.SIGNUP_TOKENS)

            if not token:
                return JSONResponse(
                    {"code": 401, "data": "Invalid signup token"}, status_code=401
                )
            elif token["uses"] >= token["max_uses"]:
                return JSONResponse(
                    {"code": 401, "data": "This token may not be used anymore"},
                    status_code=401
                )
            elif token["expiry"] <= time.time():
                return JSONResponse(
                    {"code": 401, "data": "This token is expired."}, status_code=401
                )

            db.set(
                data["username"],
                {
                    "username": data["username"],
                    "password": bcrypt.hashpw(
                        data["password"].encode(), bcrypt.gensalt()
                    ).decode(),
                    "id": nanoid.generate(),
                    "email": data["email"],
                    "used_token": data["signup_token"],
                    "created": time.time(),
                    "creation_ip": req.headers.get("CF-Connecting-IP"),
                    "sessions": [],
                    "permissions": []
                }
            )

            return JSONResponse({"code": 200, "data": "Done"}, status_code=200)
