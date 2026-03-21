# pyxfluff 2024 - 2025

from .utils.color_detection import get_color
from .utils.helpers import request_app
from AOS import globals as vars

from typing import Literal
from fastapi import Request
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

import re
import time
import httpx
import platform

from io import BytesIO
from Levenshtein import ratio

from AOS.plugins.database import db
from .models.RatingPayload import RatingPayload
import logging
try:
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet
    _HAS_PACKAGING = True
except Exception:
    _HAS_PACKAGING = False

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"


def _extract_placeid_from_request(req, default=None):
    """Extract place id from common header names used by clients.

    This accepts `Roblox-Id`, `X-Roblox-Id`, and `X-Adm-PlaceId` for
    compatibility. Returns `default` if no header present.
    """
    for h in ("Place-Id", "Roblox-Id", "X-Roblox-Id", "X-Adm-PlaceId", "X-Place-Id"):
        v = req.headers.get(h)
        if v:
            return v

    return default


class BackendAPI:
    def __init__(self, app):
        self.app = app
        self.startup_time = time.time()
        self.router = APIRouter()
        self.asset_router = APIRouter(prefix="/asset")

        self.blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
        self.blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
        self.forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

    def initialize_api_routes(self):
        @self.router.get("/ping")
        async def ping():
            return "OK"

        @self.router.get("/get_download_count")
        async def download_stats():
            return JSONResponse(
                {
                    "schemaVersion": 1,
                    "label": "Administer Downloads",
                    "message": str(len(db.get_all(db.PLACES))),
                    "color": "orange"
                },
                status_code=200
            )

        @self.router.get("/directory")
        async def app_list(req: Request, asset_type: Literal["FEATURED", "THEMES", "APPS"]):
            apps = db.get_all(db.APPS)
            final = []
            _t = time.time()

            def serialize(data):
                rating = 0
                try:
                    rating = (
                        (
                            data["Votes"]["Likes"] + data["Votes"]["Dislikes"]) == 0
                                and 0 or data["Votes"]["Likes"]
                                    / (data["Votes"]["Likes"] + data["Votes"]["Dislikes"]
                        )
                    )
                except ZeroDivisionError:
                    rating = 0  # ideally we can remove this in some months

                try:
                    final.append(
                        {
                            "name": data["Name"],
                            "short_desc": data["ShortDescription"],
                            "downloads": data["Downloads"],
                            "rating": rating,
                            "weighted_score": (data["Downloads"] * 0.6 + (rating * 0.9))
                            + data["Votes"]["Favorites"],
                            "developer": data["Developer"],
                            "last_update": data["Metadata"]["UpdatedAt"],
                            "id": data["Metadata"]["AdministerID"],
                            "object_type": data["Metadata"]["AssetType"]
                        }
                    )
                except KeyError:
                    # chances are we are dealing with a theme..
                        final.append(
                        {
                            "name": data["Name"],
                            "downloads": data["Downloads"],
                            "rating": rating,
                            "weighted_score": (data["Downloads"] * 0.6 + (rating * 0.9))
                            + data["Votes"]["Favorites"],
                            "developer": data["Developer"],
                            "last_update": data["Metadata"]["UpdatedAt"],
                            "id": data["Metadata"]["AdministerID"],
                            "object_type": data["Metadata"]["AssetType"]
                        }
                    )

            for app in apps:
                if app["administer_id"] == "__featured": continue

                serialize(app["data"])

            if asset_type == "FEATURED":
                # Render four top apps and one header, the game selects at random
                # TODO: Top app, need to develop daily installs first
                if db.get("__featured", db.APPS):
                    final = sorted(
                        final,
                        key=lambda x: (x["id"] != db.get("__featured", db.APPS), -x["weighted_score"])
                    )[:4]
                else:
                    # classic logic
                    final = sorted(final, key=lambda x: x["weighted_score"], reverse=True)[:4]

            elif asset_type == "THEMES":
                final = [x for x in final if x["object_type"] == "theme"]
            elif asset_type == "APPS":
                final = [x for x in final if x["object_type"] == "app"]
            else:
                # get all call ig?? idk maybe we want to error one day
                pass

            if final == []:
                final = [
                    {
                        "object_type": "message",
                        "text": "This AOS instance does not have any objects with the requested type."
                    }
                ]

            return JSONResponse(final, status_code=200)

        @self.router.get("/search/{search}")
        async def search(req: Request, search: str):
            apps = db.get_all(db.APPS)
            final = []
            ratio_info = {"is_ratio": False}

            search_raw = search.strip().lower()
            search = search.strip().lower().replace("type:theme", "").replace("type:app", "")

            if search_raw in [None, ""] or len(search) >= 50:
                return JSONResponse(
                    {"meta": {"_aos_search_api": "5.0"}, "index": "invalid_query"},
                    status_code=400
                )

            for app in apps:
                app = app["data"]

                if app["Metadata"]["AssetType"] == "app" and search in app["Title"].lower():
                    app["indexed"] = "name"
                    final.append(app)

                    continue

                elif ratio(search, app["Name"].lower()) >= 0.7:
                    ratio_info = {
                        "is_ratio": True,
                        "keyword": app["Name"],
                        "confidence": ratio(search, app["Name"])
                    }

                    app["ratio"] = ratio_info
                    final.append(app)

                    continue
                
                elif search == "*":
                    app["indexed"] = "wildcard"
                    final.append(app)

                    continue

                for tag in app["Tags"]:
                    if search in tag:
                        app["indexed"] = "tag"
                        final.append(app)

                        continue
                    elif ratio(search, tag) >= 0.7:
                        app["indexed"] = "tag_ratio"
                        ratio_info = {
                            "is_ratio": True,
                            "keyword": tag,
                            "confidence": ratio(search, tag)
                        }
                        final.append(app)

                        continue

            if final == []:
                return JSONResponse(
                    {"meta": {"_aos_search_api": "5.0"}, "index": "no_results"},
                    status_code=200
                )
            
            final = [app for app in final if not search_raw.startswith("type:") or app["Metadata"]["AssetType"] in search_raw]

            return JSONResponse(
                {
                    "meta": {
                        "_aos_search_api": "5.0",
                        "ratio_info": ratio_info,
                        "indexed_query": search,
                        "results": len(final)
                    },
                    "index": final
                },
                status_code=200
            )

        @self.router.post("/register-home-node")
        @self.router.post("/register")
        async def home_node(req: Request):
            placeid = _extract_placeid_from_request(req, 0)
            place = db.get(placeid, db.PLACES)

            if place is None:
                if _extract_placeid_from_request(req, 0) == 0:
                    return JSONResponse(
                        {
                            "code": 400,
                            "message": "This API endpoint cannot be used outside of a Roblox game."
                        },
                        status_code=400
                    )

                place = {
                    "Apps": [],
                    "Themes": [],
                    "Ratings": {},
                    "StartTimestamp": time.time(),
                    "StartSource": (
                        "RobloxStudio" in req.headers.get("user-agent")
                        and "STUDIO"
                        or "RobloxApp" in req.headers.get("user-agent")
                        and "CLIENT"
                        or "UNKNOWN"
                    ),
                    "HomeNode": vars.node
                }

            else:
                place["HomeNode"] = vars.node

            place["LastUpdated"] = time.time()

            db.set(placeid, place, db.PLACES)
            return JSONResponse(
                {"code": 200, "message": "Registered!"}, status_code=200
            )

        @self.router.get("/misc/get_prominent_color")
        @self.router.get("/misc/prominent-color")
        async def get_prominent_color(image_url: str):
            if not vars.is_dev:
                return get_color(BytesIO(httpx.get(image_url).content))
            else:
                # prevent vm IP leakage
                if not re.search(r"^https://tr\.rbxcdn\.com/.+", image_url):
                    return JSONResponse(
                        {"code": 400, "message": "URL must be to Roblox's CDN."},
                        status_code=400
                    )

                return get_color(BytesIO(httpx.get(image_url).content))
            
        @self.router.post("/multiget-assets")
        async def get_assets(req: Request):
            try:
                json: list[str] = await req.json()
            except Exception:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": ""
                    },
                    status_code=4030
                )


        @self.router.post("/report-version")
        async def report_version(req: Request):
            try:
                json = await req.json()
            except Exception:
                # stop fucking with the API
                return JSONResponse(
                    {
                        "code": 403,
                        "message": "Forbidden"
                    },
                    status_code=403
                )
            
            key = db.get(round(time.time() / 86400), db.REPORTED_VERSIONS)
            branch = str(json["branch"]).lower()

            # Flexible version check: permit exact versions or specifiers
            permitted = vars.state.get("permitted_versions", []) or []
            client_version = str(json.get("version", ""))

            allowed = False
            if _HAS_PACKAGING:
                try:
                    v = Version(client_version)
                except Exception:
                    v = None

                if v is not None:
                    for spec in permitted:
                        spec_s = str(spec)
                        # treat explicit specifier strings with operators as SpecifierSet
                        if any(op in spec_s for op in [">", "<", "=", "!", "~", "*"]):
                            try:
                                if v in SpecifierSet(spec_s):
                                    allowed = True
                                    break
                            except Exception:
                                continue
                        else:
                            try:
                                if v == Version(spec_s):
                                    allowed = True
                                    break
                            except Exception:
                                if spec_s == client_version:
                                    allowed = True
                                    break
            else:
                # fallback: simple membership check
                if client_version in permitted:
                    allowed = True

            if not allowed:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Administer is too old to report its version. Please update Administer."
                    },
                    status_code=400,
                )

            if not key:
                db.set(
                    f"day-{round(time.time() / 86400) - 1}",
                    {"places_len": len(db.get_all(db.PLACES))},
                    db.REPORTED_VERSIONS
                )

                key = {"internal": {}, "qa": {}, "canary": {}, "beta": {}, "stable": {}}

            if not key[branch].get(json["version"]):
                key[branch][json["version"]] = 0

            key[branch][json["version"]] += 1

            db.set(round(time.time() / 86400), key, db.REPORTED_VERSIONS)

            return JSONResponse(
                {"code": 200, "message": "Version has been recorded"}, status_code=200
            )

        @self.router.post("/app-config/upload")
        async def app_config(req: Request):
            config: {any} = await req.json()

            try:
                new_app_id = config["Metadata"]["AdministerID"]
            except KeyError:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Metadata.AdministerID must not be None and should be an AOSId2 format string"
                    },
                    status_code=400
                )

            existing = db.get(new_app_id, db.APPS)

            if existing is None:
                config["Metadata"]["CreatedAt"] = time.time()
                config["Metadata"][
                    "AOSGenerator"
                ] = f"AOS/{vars.version} AOS_NODE.{vars.node.upper()}"
            else:
                # stuff that should never be overwritten
                config["Votes"] = existing["Votes"]
                config["Downloads"] = existing["Downloads"]

            config["Metadata"]["UpdatedAt"] = time.time()

            db.set(new_app_id, config, db.APPS)

            return JSONResponse(
                {
                    "code": 200,
                    "message": "Submitted! Please allow a minute for indexes to rebuild and databases to sync."
                },
                status_code=200
            )

    def initialize_content_routes(self):
        @self.asset_router.get("/ping")
        async def ping():
            return JSONResponse({
                "code": 200,
                "data": "OK"
            }, status_code=200)

        @self.asset_router.get("/list")
        async def list_apps():
            """Return a concise list of apps in the registry.

            Each entry contains `id`, `name`, `downloads` and `object_type`.
            """
            apps = db.get_all(db.APPS)
            final = []

            for app in apps:
                if app.get("administer_id") == "__featured":
                    continue

                data = app.get("data", {})

                final.append(
                    {
                        "id": app.get("administer_id"),
                        "name": data.get("Name"),
                        "downloads": data.get("Downloads", 0),
                        "object_type": data.get("Metadata", {}).get("AssetType")
                    }
                )

            return JSONResponse({"code": 200, "data": final}, status_code=200)

        @self.asset_router.get("/{appid:str}")
        async def get_app(appid: str):
            try:
                app = request_app(appid)

                if app is None:
                    raise FileNotFoundError

                return JSONResponse(app, status_code=200)

            except Exception:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "That asset wasn't found. Maybe it was deleted while you were viewing it?"
                    },
                    status_code=404
                )

        @self.asset_router.put("/{asset_id}/vote")
        async def rate_app(asset_id: str, payload: RatingPayload, req: Request):
            # if "RobloxStudio" in req.headers.get("user-agent"):
            #     return JSONResponse(
            #         {
            #             "code": 400,
            #             "message": "studio-restricted",
            #             "user_facing_message": "Sorry, but this API endpoint may not be used in Roblox Studio. Please try it in a live game!",
            #         },
            #         status_code=400,
            #     )

            place = db.get(_extract_placeid_from_request(req), db.PLACES)
            app = request_app(asset_id)

            rating = payload.vote == 1
            is_overwrite = False

            if not place:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Bad Request",
                        "user_facing_message": "We can't find your game. Please ensure you have registered a Home Node."
                    },
                    status_code=400
                )

            if asset_id not in place["Apps"] and app["Metadata"]["AssetType"] == "app":
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Bad request",
                        "user_facing_message": "You have to install this app before you can rate it."
                    },
                    status_code=400
                )
            elif asset_id not in place["Themes"] and app["Metadata"]["AssetType"] == "theme":
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Bad request",
                        "user_facing_message": "You have to install this asset before you can rate it."
                    },
                    status_code=400
                )

            if not app:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "Not Found",
                        "user_facing_message": "That asset is not registered on this server"
                    },
                    status_code=404
                )

            if asset_id in place["Ratings"]:
                is_overwrite = True

                app["Votes"][
                    place["Ratings"][asset_id]["rating"] and "Likes" or "Dislikes"
                ] -= 1
                place["Ratings"][asset_id] = None

            place["Ratings"][asset_id] = {
                "rating": rating,
                "owned": True,
                "timestamp": time.time()
            }

            app["Votes"][rating and "Likes" or "Dislikes"] += 1
            vars.state["votes_today"] += 1

            db.set(asset_id, app, db.APPS)
            db.set(_extract_placeid_from_request(req), place, db.PLACES)

            return JSONResponse(
                {
                    "code": 200,
                    "message": "Success!",
                    "was_overwritten": is_overwrite,
                    "user_facing_message": f"Your review has been recorded, thanks for voting!{is_overwrite and ' Your previous vote for this asset has been removed.'}"
                },
                status_code=200
            )
        
        @self.asset_router.get("/{asset:str}/vote")
        async def get_vote(req: Request, asset: str):
            try:
                app = request_app(asset)
                place = db.get(_extract_placeid_from_request(req), db.PLACES)

                if app is None:
                    raise FileNotFoundError

            except Exception as e:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "That asset wasn't found. Maybe it was deleted while you were viewing it?"
                    },
                    status_code=404
                )
            
            if place is None:
                return JSONResponse(
                    {
                        "code": 401,
                        "data": "You are not registered on this server."
                    },
                    status_code=404
                )
            
            return JSONResponse(
                {
                    "code": 200,
                    "data": {
                        "liked": place["Ratings"][asset]["rating"],
                        "disliked": not place["Ratings"][asset]["rating"],
                        "favorited": False # TODO
                    }
                },
                status_code=200
            )
            
        @self.asset_router.post("/{asset_id}/install")
        async def install(req: Request, asset_id: str):
            placeid = _extract_placeid_from_request(req)
            logging.info(f"[asset.install] request place={placeid} asset={asset_id}")
            place = db.get(placeid, db.PLACES)
            logging.info(f"[asset.install] db.get returned place: {place is not None}")

            if place is None:
                logging.warning(f"[asset.install] place not found in database for placeid={placeid}")
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Place not registered. Please register your place first.",
                        "user_facing_message": "Your game is not registered. Contact the server administrator."
                    },
                    status_code=400
                )

            app = request_app(asset_id)
            if not app:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "That isn't a valid asset. Did it get removed?"
                    },
                    status_code=404
                )
            
            try:
                if app["Metadata"]["AssetType"] == "theme" and not place["Themes"]:
                    place["Themes"] = []
            except KeyError:
                place["Themes"] = []

            if (
                asset_id
                in place[app["Metadata"]["AssetType"] == "app" and "Apps" or "Themes"]
            ):
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "resource-limited",
                        "user_facing_message": "You may only install an asset once."
                    },
                    status_code=400
                )
            
            place[app["Metadata"]["AssetType"] == "app" and "Apps" or "Themes"].append(
                asset_id
            )
            app["Downloads"] += 1

            logging.info(f"[asset.install] place before save - Apps: {place.get('Apps', [])}, Themes: {place.get('Themes', [])}")
            
            res_app = db.set(asset_id, app, db.APPS)
            res_place = db.set(placeid, place, db.PLACES)

            logging.info(f"[asset.install] db.set app result: {res_app}")
            logging.info(f"[asset.install] db.set place result: {res_place}")

            vars.state["downloads_today"] += 1

            return JSONResponse(
                {"code": 200, "message": "success", "user_facing_message": "Success!"},
                status_code=200
            )

        @self.asset_router.post("/{asset_id}/uninstall")
        async def uninstall(req: Request, asset_id: str):
            placeid = _extract_placeid_from_request(req)
            logging.info(f"[asset.uninstall] request place={placeid} asset={asset_id}")
            place = db.get(placeid, db.PLACES)

            if place is None:
                if not placeid:
                    return JSONResponse(
                        {
                            "code": 400,
                            "message": "This API endpoint cannot be used outside of a Roblox game."
                        },
                        status_code=400
                    )

                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Place not registered.",
                        "user_facing_message": "Your game is not registered. Contact the server administrator."
                    },
                    status_code=400
                )

            app = request_app(asset_id)
            if not app:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "That isn't a valid asset. Did it get removed?"
                    },
                    status_code=404
                )

            key = app["Metadata"]["AssetType"] == "app" and "Apps" or "Themes"

            if asset_id not in place.get(key, []):
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "not-installed",
                        "user_facing_message": "You must install this asset before you can uninstall it."
                    },
                    status_code=400
                )

            try:
                place[key].remove(asset_id)
            except Exception:
                place[key] = [a for a in place.get(key, []) if a != asset_id]

            if isinstance(app.get("Downloads"), int) and app.get("Downloads", 0) > 0:
                app["Downloads"] -= 1

            logging.info(f"[asset.uninstall] place before save - Apps: {place.get('Apps', [])}, Themes: {place.get('Themes', [])}")

            res_app = db.set(asset_id, app, db.APPS)
            res_place = db.set(placeid, place, db.PLACES)

            logging.info(f"[asset.uninstall] db.set app result: {res_app}")
            logging.info(f"[asset.uninstall] db.set place result: {res_place}")

            return JSONResponse(
                {"code": 200, "message": "success", "user_facing_message": "Uninstalled."},
                status_code=200
            )

        @self.asset_router.get("/installed")
        async def get_installed(req: Request, placeid: str | None = None):
            """Return installed Apps and Themes for a place.

            Use `Roblox-Id` header if `placeid` query param is not provided.
            """
            # prefer explicit query param, fallback to header
            if not placeid:
                placeid = req.headers.get("Roblox-Id")

            if not placeid:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "missing-placeid",
                        "user_facing_message": "No place id provided in query or Roblox-Id header."
                    },
                    status_code=400,
                )

            place = db.get(placeid, db.PLACES)
            if place is None:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "Place not registered on this server."
                    },
                    status_code=404,
                )

            return JSONResponse(
                {
                    "code": 200,
                    "data": {
                        "Apps": place.get("Apps", []),
                        "Themes": place.get("Themes", [])
                    }
                },
                status_code=200,
            )

        @self.asset_router.get("/{asset:str}/monetization")
        async def get_paid_status(req: Request, asset: str):
            try:
                app = request_app(asset)

                if app is None:
                    raise FileNotFoundError

            except Exception:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "App not found on this server"
                    },
                    status_code=404
                )
            
            return JSONResponse(
                {
                    "code": 200,
                    "data": {
                        "is_paid_asset": app["RequirePayment"] == True,
                        "is_for_sale": app["GamePassID"] != -1,
                        "pass_id": app["GamePassID"]
                    }
                },
                status_code=200
            )


# @router.get("/logs/{logid:str}")
# def get_log(req: Request, logid: str):
#    return db.get(logid, db.LOGS)
