# pyxfluff 2025

import AOS.deps.il as il

from AOS import app
from AOS.plugins.database import db

import httpx
import orjson
import nanoid

from pathlib import Path
from fastapi import Request
from datetime import datetime
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

plugin_router = APIRouter(prefix="/feedback-assistant")

try:
    webhook_url = orjson.loads(
        (Path(__file__).resolve().parent / "config/FeedbackAssistant.json").read_text()
    )["webhook_url"]
except FileNotFoundError:
    il.cprint(
        "FeedbackAssistant config not found! Webhook logging will NOT be active.", 34
    )


@plugin_router.get("/ping")
async def ping():
    return "OK"


@plugin_router.post("/submit")
async def submit_feedback(req: Request):
    is_blocked = db.get(
        req.headers.get("Roblox-Id", 0), db.ABUSE_LOGS
    )  # using abuse_logs bc i can lmao

    if is_blocked:
        return JSONResponse(
            {
                "code": 401,
                "title": "Blocked",
                "body": "Sorry, but your game has been blocked from using the feedback reporter on this instance due to abuse."
            },
            status_code=401
        )

    if (await req.body()) == b"":
        return JSONResponse(
            {
                "code": 400,
                "title": "Bad input",
                "body": "Incomplete or bad data, please ensure all fields are filled correctly."
            },
            status_code=400
        )

    json = await req.json()
    db_key = nanoid.generate()

    db.set(
        db_key,
        {
            "place_id": req.headers["Roblox-Id"],
            "server_logs": json["ServerLogs"][250:],
            "client_logs": json["ClientLogs"][250:]
        },
        db.V2_LOGS
    )

    try:
        if (  # this is kinda overkill, but i don't want abuse
            len(json["Comment"]) >= 700
            or len(json["Administer"]) >= 300
            or len(json["What"] + json["Where"] + json["Priority"]) >= 150
            or db.get(req.headers["Roblox-Id"], db.PLACES) is None
        ):
            return JSONResponse(
                {
                    "code": 400,
                    "title": "Bad input",
                    "body": "Illegitimate data was received that the server cannot process."
                },
                status_code=400
            )
    except KeyError:
        return JSONResponse(
            {
                "code": 400,
                "title": "Bad input",
                "body": "Incomplete or bad data, please ensure all fields are filled correctly."
            },
            status_code=400
        )

    httpx.post(
        url=webhook_url,
        json={
            "content": "New report received",
            "embeds": [
                {
                    "title": "Report",
                    "description": f"""
                    ```yaml
- Is studio: {json["IsStudio"]}
- Administer Version data: {json["Administer"]}
- Place: {req.headers["Roblox-Id"]}
- Issue: {json["What"]} in {json["Where"]} with priority {json["Priority"]}
- User comment: {json["Comment"].strip()}
- Database logs key: {db_key}
```""".strip(),
                    "color": 5814783,
                    "timestamp": datetime.now().isoformat(timespec="milliseconds")
                    + "Z"
                }
            ],
            "username": "Administer V2 Feedback Agent",
            "attachments": []
        }
    )

    return JSONResponse(
        {
            "code": 200,
            "title": "Report submitted",
            "body": f"Thank you for helping Administer! We have recorded your feedback. If you have any further questions, let our support staff know with your unique ticket ID: `{db_key}`"
        },
        status_code=200
    )


app.include_router(plugin_router)
