# pyxfluff 2024-2025 - 2025

import AOS.deps.il as il
import os
import sys
import orjson
import logging
import asyncio

from sys import argv
from contextlib import asynccontextmanager

from fastapi import FastAPI
from uvicorn import Config, Server


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        il.cprint(
            f"[✓] Done! Serving {len(app.routes)} routes on http://{argv[2]}:{argv[3]}.",
            32,
        )
    except IndexError:
        il.cprint(
            f"[✓] Done! Serving {len(app.routes)} routes on http://{globals.def_host}:{globals.def_port}.",
            32,
        )

    try:
        yield
    finally:
        il.cprint("[✗] Goodbye, shutting things off...", 31)

        # if input(
        #    "Would you like to rebuild and restart the app? [[y]es/[n]o/^C] "
        # ).lower() in ["y", "yes"]:
        #    il.cprint("[-] Respawning process after an upgrade, see you soon..", 32)
        #    Popen(
        #        f"uv pip install -e . --force-reinstall && aos serve {argv[2]} {argv[3]}",
        #        shell=True,
        #    )


class AOSVars:
    def __init__(self):
        files = ["../._config.json", "../._aos.json", "../._version_data.json"]
        config, aos_config, version_data = (
            orjson.loads(open(os.path.join(os.path.dirname(__file__), f), "r").read())
            for f in files
        )

        self.instance_name = config["instance_name"]
        self.is_dev = config["is_dev"]
        self.enable_bot_execution = config["enable_bot_execution"]

        self.logging_location = config["logging_location"]
        self.banner = config["banner"]

        self.dbattrs = config.get("dbattrs", {})
        self.security = config.get("security", {})
        self.flags = config.get("flags", {})

        self.version = aos_config["version"]
        self.workers = aos_config["workers"]

        self.def_host = aos_config["default_host"]
        self.def_port = aos_config["default_port"]

        self.state = aos_config.get("state", {})

        self.versions = version_data


class AOSError(Exception):
    def __init__(self, message):
        il.cprint(message, 31)
        sys.exit(1)


globals = AOSVars()


def load_fastapi_app():
    app = FastAPI(
        debug=globals.is_dev,
        title=f"Administer App Server {globals.version}",
        description="An Administer app server instance for distributing Administer applications.",
        version=globals.version,
        openapi_url="/openapi",
        lifespan=lifespan,
    )

    try:
        config = Config(
            app=app, host=argv[2], port=int(argv[3]), workers=globals.workers
        )
    except IndexError:
        config = Config(
            app=app,
            host=globals.def_host,
            port=globals.def_port,
            workers=globals.workers,
        )

    logging.getLogger("uvicorn").disabled = True
    logging.getLogger("uvicorn.access").disabled = True

    il.cprint("[✓] Uvicorn loaded", 32)
    il.cprint("[-] Importing modules...", 32)

    il.cprint("[-] Loading database...", 32)
    try:
        from .database import db
    except Exception:
        il.cprint(
            "\n[x]: failed to connect to pymongo! please ensure your database URL is correct and you are able to connect to it.",
            31,
        )
        raise AOSError("database connection failed!")
    else:
        il.cprint("[✓] Database OK", 32)

    from .routes.backend import BackendAPI
    from .routes.public import PublicAPI
    from .routes.frontend import Frontend
    from .middleware import Middleware

    backend_api = BackendAPI(app)
    public_api = PublicAPI(app)

    backend_api.initialize_api_routes()
    backend_api.initialize_content_routes()
    public_api.initialize_routes()

    app.include_router(backend_api.router, prefix="/api")
    app.include_router(backend_api.asset_router, prefix="/api")
    app.include_router(public_api.router, prefix="/pub")

    frontend = Frontend(app)
    frontend.initialize_frontend()

    middleware = Middleware(app)
    middleware.init()

    if globals.enable_bot_execution:
        from .utils.release_bot import bot, token

        asyncio.gather(bot.start(token))

    try:
        Server(config).run()
    except KeyboardInterrupt:
        il.cprint("[✓] Cleanup job OK", 31)

    return app
