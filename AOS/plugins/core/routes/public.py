# pyxfluff 2024-2025

from AOS import globals

from fastapi.responses import JSONResponse

import time
import platform

from sys import version
from fastapi import Request, APIRouter

from AOS.plugins.database import db

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"


class PublicAPI:
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
                    "instance_name": globals.instance_name,
                    "server": "AdministerAppServer",
                    "api_version": globals.version,
                    "uptime": time.time() - self.t,
                    "engine": version,
                    "system": sys_string,
                    "workers": globals.workers,
                    "has_secrets": len(db.get_all(db.SECRETS)) not in [0, None],
                    "total_apps": len(db.get_all(db.APPS)),
                    "is_dev": globals.is_dev,
                    "banner": globals.banner,
                    "supported_versions": globals.state["permitted_versions"]
                },
                status_code=200
            )

        @self.router.get("/logs/{logid}")
        def get_log(logid: str):
            log = db.get(logid, db.LOGS)
            if log is None:
                return JSONResponse(
                    {"error": "This logfile does not exist."}, status_code=404
                )
            return log

        @self.router.get("/versions")
        def administer_versions(req: Request):
            current_vers = req.headers.get("X-Adm-Version")

            try:
                globals.versions["versions"][current_vers][
                    "_retrieved_at"
                ] = time.time()
            except KeyError:
                return JSONResponse(
                    {"message": "That is not a valid version."}, status_code=400
                )

            return JSONResponse(
                {
                    "latest_version": globals.versions["_latest_versions"][
                        req.headers.get("X-Adm-Branch")
                    ],
                    "your_version": {
                        "version": current_vers,
                        "branch": req.headers.get("X-Adm-Branch"),
                        "featureset": globals.versions["versions"][current_vers][
                            "featureset"
                        ],
                        "is_outdated": globals.versions["versions"][current_vers][
                            "is_outdated"
                        ]
                    },
                    "versions": globals.versions["versions"]
                }
            )
