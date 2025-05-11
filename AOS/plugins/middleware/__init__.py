# pyxfluff 2024 - 2025

from AOS.deps import il
from http import HTTPStatus
from fastapi import Response, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import time
import httpx

from types import FunctionType
from collections import defaultdict

from AOS import globals, app
from AOS.plugins.database import db

known_good_ips  = []
limited_ips     = defaultdict(list)
mem_incidents   = defaultdict(list)
mem_blocked_ips = defaultdict(list)

blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

auth_key = db.get("__ENV_AUTH__", db.SECRETS)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request,
                       call_next: FunctionType) -> Response:
        if request.headers.get("CF-Connecting-IP") in forbidden_ips:
            return JSONResponse(
                    {
                        "code": 400,
                        "message": "Sorry, but your IP has been blocked due to suspected abuse. Please reach out if this was a mistake." 
                    },
                    status_code=400
                )

        try:
            if (
                str(request.url).split("/")[4] == "app-config"
                and request.headers.get("X-Adm-Auth", "") == auth_key
            ):
                return await call_next(request)
            elif (
                str(request.url).split("/")[4] == "app-config"
                and request.headers.get("X-Adm-Auth", "") != auth_key
            ):
                return JSONResponse(
                    {"code": 401, "message": "Bad authorization."}, 401)
        except IndexError:
            pass

        if globals.security["use_roblox_lock"]:
            if str(request.url).split(
                    "/")[4] in globals.state["unchecked_endpoints"]:
                return await call_next(request)

            if (
                not request.headers.get("Roblox-Id")
                and not request.url == "http://administer.notpyx.me/"
            ):
                return JSONResponse(
                        {
                            "code": 400,
                            "message": "This App Server is only accepting requests from Roblox game servers."
                        },
                        status_code=400
                    )

            if request.headers.get("CF-Connecting-IP") in known_good_ips:
                # all is well
                return await call_next(request)

            elif "RobloxStudio" in request.headers.get("user-agent"):
                # Limit this on a per-API basis
                return await call_next(request)

            elif (
                not httpx.get(
                    f"http://ip-api.com/json/{request.headers.get('CF-Connecting-IP')}?fields=status,isp"
                ).json()["isp"]
                == "Roblox"
            ):
                db.set(
                    request.headers.get("CF-Connecting-IP"),
                    db.ABUSE_LOGS,
                    {
                        "timestamp": time.time(),
                        "ip-api_full_result": httpx.get(
                            f"http://ip-api.com/json/{request.headers.get('CF-Connecting-IP')}?fields=status,message,country,regionName,isp,org,mobile,proxy,hosting,query"
                        ).json(),
                        "roblox-id": request.headers.get("Roblox-Id"),
                        "user-agent": request.headers.get("user-agent", "unknown"),
                        "endpoint": request.url,
                    },
                )

                forbidden_ips.append(request.headers.get("CF-Connecting-IP"))
                db.set("BLOCKED_IPS", forbidden_ips, db.ABUSE_LOGS)

                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Your IP has been blocked due to suspected API abuse."
                    },
                    status_code=401
                )

            else:
                known_good_ips.append(request.headers.get("CF-Connecting-IP"))

        if globals.security["use_api_keys"] and not request.headers.get(
            "X-Administer-Key"
        ):
            return JSONResponse(
                {"code": 400, "message": "A valid API key must be used."},
                status_code=401
            )

        elif globals.security["use_api_keys"] and not db.get(
            request.headers.get("X-Administer-Key"), db.API_KEYS
        ):
            return JSONResponse(
                {"code": 400, "message": "Please provide a valid API key."},
                status_code=401
            )

        elif globals.security["use_api_keys"]:
            api_key_data = db.get(
                request.headers.get("X-Administer-Key"), db.API_KEYS)

            if (
                api_key_data.disabled
                or api_key_data.registered_to in blocked_users
                or api_key_data.registered_game in blocked_games
            ):
                return JSONResponse(
                        {
                            "code": 400,
                            "message":
                            "Your API key has been disabled due to possible abuse. To reach out to the API team please join the discord and make a ticket (/discord).", 
                        },

                        status_code=400
                    )

        if globals.security["use_sessions"] and not request.headers.get(
            "X-Administer-Session"
        ):
            return JSONResponse(
                {"code": 400, "message": "A valid session token is required."},
                status_code=400
            )

        return await call_next(request)


class RateLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request,
                       call_next: FunctionType) -> Response:
        cf_ip = request.headers.get("CF-Connecting-IP")

        if cf_ip in mem_blocked_ips:
            print("This IP is blocked in memory.")
            return JSONResponse(
                {"code": 400, "message": "Sorry, you have been blocked."},
                status_code=400
            )

        if not cf_ip:
            # development install?
            globals.state["requests"] += 1
            return await call_next(request)

        limited_ips[cf_ip] = [
            timestamp
            for timestamp in limited_ips[cf_ip]
            if timestamp
            > time.time() - globals.security["ratelimiting"]["reset_timeframe"]
        ]

        if len(limited_ips[cf_ip]) >= globals.security["ratelimiting"][
                "max_reqs"]:
            return JSONResponse(
                {"code": 400, "message": "You are being rate limited, please try again later."},
                status_code=400
            )

        limited_ips[cf_ip].append(time.time())

        globals.state["requests"] += 1

        return await call_next(request)


class Logger(BaseHTTPMiddleware):
    async def dispatch(self, req: Request,
                       call_next: FunctionType) -> Response:
        cf_ip = req.headers.get("CF-Connecting-IP")

        t = time.time()
        res = await call_next(req)

        il.request(
            str(req.url),
            req.headers.get("CF-Connecting-IP"),
            f"Code {res.status_code} ({HTTPStatus(res.status_code).phrase})",
            str(res.status_code).startswith("2") and 32 or 31,
            time.time() - t,
            f"PlaceID: {req.headers.get('Roblox-Id') or 'Not a Roblox place'}\n\nRatelimiting data: {len(limited_ips[cf_ip])}/{globals.security['ratelimiting']['max_reqs']} used",
            req.method,
        )

        res.headers["X-Powered-By"] = f"AdministerAppServer; AOS/{globals.version}"
        res.headers["Server-Timing"] = f"{res.headers.get('Server-Timing', '')}full_process;dur={str((time.time() - t) * 1000)}"

        return res


class Middleware:
    def __init__(self):
        il.cprint("[✓] Middleware loaded, following rules in ._aos.json!", 34)

    def init(self):
        app.add_middleware(AuthMiddleware)
        app.add_middleware(RateLimiter)
        app.add_middleware(Logger)


middleware = Middleware()

middleware.init()
