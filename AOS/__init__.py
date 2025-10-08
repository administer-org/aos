# pyxfluff 2024 - 2025

import AOS
import AOS.deps.il as il

from AOS.models.AOSConfig import AOSConfig
from AOS.models.CoreConfig import CoreConfig


import re
import sys
import orjson
import logging
import asyncio

from sys import argv
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from uvicorn import Config, Server, __version__
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        il.cprint(
            f"[✓] Done! Serving {len(app.routes)} routes on http://{argv[2]}:{argv[3]}.",
            32
        )
    except IndexError:
        il.cprint(
            f"[✓] Done! Serving {len(app.routes)} routes on http://{globals.def_host}:{globals.def_port} (using default host/port).",
            32
        )

    try:
        yield
    finally:
        il.cprint("[✗] Goodbye, Exiting AOS...", 31)
        # shutdown data upload TODO


class AOSVars:
    def remove_comments(self, path):
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError

        text = p.read_text(encoding="utf-8")
        text = re.sub(r'(?<!:)//.*', '', text)
        text = text.strip()

        try:
            return orjson.loads(text)
        except Exception as e:
            raise ValueError(f"Failed to parse AOS config: {e}")

    def __init__(self):
        try:
            config, aos_config, version_data = (
                self.remove_comments(Path(__file__).parent / f)
                for f in ["../._config.jsonc", "../._aos.json", "../._version_data.json"]
            )
        except Exception as c_exception:
            # try again with legacy .json
            il.cprint(
                f"[!] Failed to read ._config.json, please migrate ASAP. Falling back to legacy file. {c_exception}", 
                33
            )

            try:
                config, aos_config, version_data = (
                    orjson.loads((Path(__file__).parent / f).read_text())
                    for f in ["../._config.json", "../._aos.json", "../._version_data.json"]
                )
            except Exception as e:
                il.cprint("[!] Welcome to AOS!", 34)
                il.cprint("    > It seems like your environment has not been setup.", 32)
                il.cprint(
                    "       > If you are installed via PyPI or on Windows, run the following:",
                    32
                )
                il.cprint("         > aos setup run", 33)
                il.cprint(
                    "       > If you are running on a unix-like system then please run", 32
                )
                il.cprint("         > ./Install_AOS", 33)
                raise AOSError(f"exiting: {e}", True)

        for config in [
            CoreConfig(**config).model_dump().items(),
            AOSConfig(**aos_config).model_dump().items()
        ]:
            for k, v in config:
                setattr(self, k, v)

        self.versions = version_data


class AOSError(Exception):
    def __init__(self, message, exit: Optional[bool]):
        il.cprint(message, 31)

        if exit is None or exit:
            sys.exit(1)


globals = AOSVars()
app = None


def load_fastapi_app():
    il.cprint("[-] Loading FastAPI..", 33)
    AOS.app = FastAPI(
        debug=globals.is_dev,
        title=f"Administer AOS ({globals.version})",
        description="An AOS instance for distributing Administer applications and serving other plugins.\n\nThe documentation here will only show URLs. For actual API reference, please refer to https://docs.admsoftware.org",
        version=globals.version,
        openapi_url="/_misc/openapi.json",
        lifespan=lifespan
    )

    app = AOS.app

    il.cprint(f"[-] spawning uvicorn {__version__} with {globals.workers} cpu threads", 34)

    try:
        config = Config(
            app=app, host=argv[3], port=int(argv[4]), workers=globals.workers
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
