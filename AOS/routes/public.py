# pyxfluff 2024-2025

from AOS import globals

from fastapi.responses import JSONResponse

import time
import platform

from sys import version
from fastapi import Request, APIRouter

from AOS.database import db

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"


class PublicAPI():
    def __init__(self, app):
        self.app = app
        self.t = time.time()

        self.router = APIRouter()

    def initialize_routes(self):
        @self.router.get("/ping")
        def test():
            return "OK"

        @self.router.get("/.administer")
        async def administer_metadata():
            return JSONResponse(
                {
                    "status": "OK",
                    "code": 200,
                    "server": "AdministerAppServer",
                    "uptime": time.time() - self.t,
                    "engine": version,
                    "system": sys_string,
                    "api_version": globals.version,
                    "target_administer_versions": globals.state["permitted_versions"],
                    "is_dev": globals.is_dev,
                    "has_secrets": len(db.get_all(db.SECRETS)) not in [0, None],
                    "total_apps": len(db.get_all(db.APPS)),
                    "banner": db.get("banner_text", db.APPS),
                    "banner_color": "#fffff",
                },
                status_code=200,
            )

        @self.router.get("/logs/{logid}")
        def get_log(logid: str):
            log = db.get(logid, db.LOGS)
            if log is None:
                return JSONResponse({"error": "This logfile does not exist."}, status_code=404)
            return log

        @self.router.get("/versions")
        def administer_versions(req: Request):
            # hardcoded for now :3
            return JSONResponse(
                {
                    "provided_information": {
                        "branch": "STABLE",
                        "version": "1.2.3",
                        "outdated": True,
                        "can_update_to": {"branch": "STABLE", "name": "2.0.0"},
                        "featureset": {
                            "apps": {
                                "can_download": True,
                                "can_install_new": False,
                                "can_access_marketplace": True,
                            },
                            "administer": {"can_auto_update": True, "can_report_version": True},
                            "misc": {"supports_ranks": ["v2"]},
                        },
                    },
                    "versions": {
                        "2.0.0": {
                            "latest": True,
                            "available_to": ["STABLE", "CANARY"],
                            "distributed_via": ["git", "roblox", "pesde", "aos-us_central"],
                            "released": time.time(),
                            "hash": "7c8e62d",
                            "logs": ["a", "b", "c"],
                        },
                        "2.1.0-7c8e62d": {
                            "latest": False,
                            "available_to": ["git"],
                            "distributed_via": ["git"],
                            "released": time.time(),
                            "hash": "7c8e62d",
                            "logs": [
                                "This is a prerelease directly from Git, as such we have no information."
                            ],
                        },
                    },
                }
            )
