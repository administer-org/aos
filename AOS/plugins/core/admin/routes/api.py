# pyxfluff 2025

import re
import time
import bcrypt
import nanoid

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from AOS.plugins.database import get_web_database

db = get_web_database()


def validate(password):
    pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
    return re.match(pattern, password) is not None


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
                    status_code=401,
                )
            elif user.get("inactive", False):
                return JSONResponse(
                    {"code": 401, "data": "Your account has been deactivated."},
                    status_code=401,
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
                "browser": req.headers.get("User-Agent"),
                "expiry": data["stayLoggedIn"] and 62899200 or time.time() + 86400 # 2 years is ample time
            }

            user["sessions"].append(f"{user["username"]}-{session["id"]}")
            user["seen"] = time.time()

            db.set(data["username"], user, db.USERS)
            db.set(f"{user["username"]}-{session["id"]}", session, db.SESSIONS)

            response = JSONResponse(
                {"code": 200, "data": "Redirecting..."}, status_code=200
            )

            response.set_cookie(
                key="AOS_-SessionAuth",
                value=f"{user["username"]}-{session["id"]}",
                max_age=data["stayLoggedIn"] and 62899200 or 86400,
                httponly=True,
                samesite="strict",
                secure=False
            )

            return response

        @self.router.post("/signup")
        async def signup(req: Request):
            db.set(
                "abc",
                {
                    "uses": 0,
                    "max_uses": 1,
                    "users": [],
                    "expiry": 99999999999999,
                    "creator": "system"
                },
                db.SIGNUP_TOKENS
            )
            data = await req.json()
            token = db.get(data["signup_token"], db.SIGNUP_TOKENS)

            data["username"] = data["username"].strip()

            if not token:
                return JSONResponse(
                    {"code": 400, "data": "Invalid signup token"}, status_code=400
                )
            elif token["uses"] >= token["max_uses"]:
                return JSONResponse(
                    {"code": 400, "data": "This token may not be used anymore"},
                    status_code=400,
                )
            elif token["expiry"] <= time.time():
                return JSONResponse(
                    {"code": 400, "data": "This token is expired."}, status_code=400
                )

            # holy validation
            if db.get(data["username"], db.USERS) is not None:
                return JSONResponse(
                    {"code": 400, "data": "That username is taken."}, status_code=400
                )
            elif not validate(data["password"]):
                return JSONResponse(
                    {
                        "code": 400,
                        "data": "That password is too weak. Please make sure it has one upper and lowercase letter, one digit, has one special character, and is 8 characters long.",
                    },
                    status_code=400
                )
            elif data["username"] in ["system", "aos", "administer"]:
                return JSONResponse(
                    {"code": 400, "data": "That username is reserved."}, status_code=400
                )
            elif len(data["username"]) <= 3:
                return JSONResponse(
                    {"code": 400, "data": "That username is too short."},
                    status_code=400
                )
            elif len(data["username"]) >= 30:
                return JSONResponse(
                    {"code": 400, "data": "That username is too long."}, status_code=400
                )
            elif data["username"] in data["password"]:
                return JSONResponse(
                    {"code": 400, "data": "Your username can't contain your password."},
                    status_code=400
                )
            elif not re.match(r"^[a-zA-Z0-9_.!,\-]+$", data["username"]):
                return JSONResponse(
                    {
                        "code": 400,
                        "data": "Please keep your username limited to standard latin characters."
                    },
                    status_code=400
                )
            elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", data["email"]):
                return JSONResponse(
                    {"code": 400, "data": "That is not a real email."}, status_code=400
                )

            token["uses"] += 1
            token["users"].append(data["username"])

            db.set(data["signup_token"], token, db.SIGNUP_TOKENS)

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
                    "permissions": [],
                    "inactive": False,
                    "seen": -1,
                },
                db.USERS,
            )

            return JSONResponse(
                {"code": 200, "data": "Created, redirecting..."}, status_code=200
            )
