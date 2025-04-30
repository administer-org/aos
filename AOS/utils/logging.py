# pyxfluff 2025

from subprocess import run
from pathlib import Path

from AOS import globals, AOSError


def process_command(command):
    print(command)

    match command:
        case "clear":
            if input(
                "Are you sure you would like to clear the logfile? [y/n] > "
            ).lower() not in ["y", "yes"]:
                return

            with open(globals.logging_location, "w") as log:
                log.write("")
                log.close()

            print("Done!")

        case "read":
            run(["less", globals.logging_location])

        case _:
            raise AOSError(
                "Command not found! Please use `aos help` for more information.")
