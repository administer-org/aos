# pyxfluff 2025

from fastapi import Response, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from types import FunctionType

from AOS.plugins.database import db

async def DiscordAuthentication(
        request: Request
    ):
    return
    place_id = request.headers.get("Roblox-Id")
    print(place_id)

    if not place_id:
        raise HTTPException(status_code=401, detail="You must add a place ID.")
    
    if "/api" in str(request.url):
        secret = db.get(place_id, db.DISCORD_REMOTE_SECRETS)

        print(secret, request.headers.get("X-Adm-Secret"), secret != request.headers.get("X-Adm-Secret", ""))

        if not secret:
            raise HTTPException(status_code=401, detail="You must generate a secret before using this API.")
        elif request.headers.get("X-Adm-Secret", "") == "":
            raise HTTPException(status_code=401, detail="You must provide a secret.")
        elif secret != request.headers.get("X-Adm-Secret", ""):
            raise HTTPException(status_code=401, detail="Invalid, expired, or incorrect secret.")
