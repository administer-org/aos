# pyxfluff 2024 - 2025

import il
import asyncio
import logging
import platform

from sys import argv
from pathlib import Path
from fastapi import FastAPI

from AOS import AOSError, globals as var

if not var.is_dev:
    il.set_log_file(Path("/etc/adm/log"))
    logging.getLogger("uvicorn.error").disabled = True


def serve_web_server():
    il.cprint("[-] Loading Uvicorn...", 32)

    from AOS import load_fastapi_app

    app = load_fastapi_app()


def help_command():
    il.cprint("AOS Commands", 32)

    il.cprint(
        """* aos serve [HOST] [PORT]
        Serves the full AOS webserver.""",
        34,
    )
    il.cprint(
        """        [HOST]: The HTTP IP to host on.
        [PORT]: The port to serve uvicorn on.
    """,
        32,
    )

    il.cprint(
        """* aos help
        Displays this command.
    """,
        34,
    )

    il.cprint(
        """* aos usage
        Loads usage information. (dev only)
    """,
        34,
    )

    il.cprint(
        """* aos dbot [TOKEN]
        Loads the Discord bot.""",
        34,
    )
    il.cprint(
        """        [TOKEN] (optional): The token the bot uses. Defaults to SECRETS.DISCORD_BOT.
    """,
        32,
    )

    il.cprint(
        """* aos db
        Loads the MongoDB Explorer script. Connects to the database defined in AOSVars.
    """,
        34,
    )


il.box(85, f"Administer AOS (marketplace server)", f"v{var.version}")

if __name__ != "__main__":
    # il.cprint("AOS is running as a module, disregarding.", 31)
    # return
    pass

try:
    _ = argv[1]
except IndexError:
    help_command()
    raise AOSError("A command is required. Showing help command.")

match argv[1]:
    case "serve":
        try:
            serve_web_server()
        except IndexError:
            il.cprint(
                "\n[x]: incorrect usage of `serve`\n\nusage: AOS serve [host] [port]",
                31,
            )

    case "help":
        help_command()

    case "usage":
        try:
            from AOS.reports.GraphReporter import *
        except ImportError:
            il.cprint(
                "\n[x]: This command may only be used by staff",
                31,
            )

    case _:
        il.cprint("\n[x]: command not found, showing help", 31)
        help_command()


def main():
    # diseregard
    pass
