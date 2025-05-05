# pyxfluff 2024-2025 - 2025

import AOS.deps.il as il

import AOS

import sys
import orjson
import logging
import asyncio

from sys import argv
from pathlib import Path
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
            f"[✓] Done! Serving {len(app.routes)} routes on http://{globals.def_host}:{globals.def_port} (using default host/port).",
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
        try:
            files = [
                "../._config.json",
                "../._aos.json",
                "../._version_data.json"]
            config, aos_config, version_data = (
                orjson.loads((Path(__file__).parent / f).read_text())
                for f in files)
        except Exception as e:
            il.cprint("[!] Welcome to AOS!", 34)
            il.cprint(
                "    > It seems like your enviornment has not been setup.", 32)
            il.cprint(
                "       > If you are installed via PyPI or on Windows, run the following:", 32)
            il.cprint("         > aos setup", 33)
            il.cprint(
                "       > If you are running on a unix-like system then please run", 32)
            il.cprint("         > ./Install_AOS", 33)
            raise AOSError(f"exiting: {e}")

        self.instance_name = config["instance_name"]
        self.is_dev = config["is_dev"]
        self.enable_bot_execution = config["enable_bot_execution"]
        self.reporting_url = config["report_webhook_url"]

        self.logging_location = config["logging_location"]
        self.banner = config["banner"]

        self.dbattrs = config.get("dbattrs", {})
        self.security = config.get("security", {})
        self.flags = config.get("flags", {})

        self.plugin_load_order = aos_config.get("plugin_load_order", {})

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
app = None


def load_fastapi_app():
    il.cprint("[-] Loading Uvicorn..", 33)
    AOS.app = FastAPI(
        debug=globals.is_dev,
        title=f"Administer App Server {
            globals.version}",
        description="An Administer app server instance for distributing Administer applications.",
        version=globals.version,
        openapi_url="/openapi",
        lifespan=lifespan)

    app = AOS.app

    try:
        config = Config(
            app=app, host=argv[2], port=int(argv[3]), workers=globals.workers
        )
    except IndexError:
        config = Config(
            app=app,
            host=globals.def_host,
            port=globals.def_port,
            workers=globals.workers
        )

    logging.getLogger("uvicorn").disabled = True
    logging.getLogger("uvicorn.access").disabled = True

    il.cprint("[✓] Uvicorn loaded", 32)
    if globals.enable_bot_execution:
        from .utils.release_bot import bot, token

        asyncio.gather(bot.start(token))

    def run():
        try:
            Server(config).run()
        except KeyboardInterrupt:
            il.cprint("[✓] Cleanup job OK", 31)

    AOS.run_server = run

    return True
