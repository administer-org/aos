# pyxfluff 2024 - 2025

import AOS
import AOS.deps.il as il
import AOS.plugin_loader as Plugin

from AOS import AOSError, globals as var
from AOS.utils import logging as logging

from pathlib import Path
from sys import argv

import orjson
import logging as Pythonlogging
import threading

if var.logging_location is None:
    var.logging_location = "/etc/adm/log"
    il.cprint("config.logging_location is unset, defaulting to `/etc/adm/log`", 33)

if Path(var.logging_location).is_file() is not True:
    il.cprint(
        "Your logfile (._config.json\\logging_location) is not a file! Please ensure it exists and is not a directory.",
        24,
    )

if not var.is_dev:
    try:
        il.set_log_file(Path(var.logging_location))
        Pythonlogging.getLogger("uvicorn.error").disabled = True
    except Exception as e:
        il.cprint(
            f"Failed to write to the logfile! Please make sure you have properly initialized AOS ({e}).",
            24,
        )


def help_command():
    plugins = Plugin.get_plugins(False)
    plugins_autoload = Plugin.get_plugins(True)
    commandless_plugins = 0
    il.cprint("Commands", 32)

    for config in plugins.values():
        if len(config.get("commands", {}).items()) == 0: 
            commandless_plugins += 1

    il.cprint(f"│  \033[1m{len(plugins)}\033[0m\033[32m plugins are installed", 32)
    il.cprint(f"│  \033[1m{commandless_plugins}\033[0m\033[32m of which have no commands (not displayed)", 32)
    il.cprint(f"└> and \033[1m{len(plugins_autoload)}\033[0m\033[32m load automatically!", 32)

    il.box(50, "Built-in", "1 command")

    il.cprint(
        """* aos help
        Lists plugin help commands.""",
        34
    )

    for config in plugins.values():
        if len(config.get("commands", {}).items()) == 0: return
        il.box(
            50,
            config["name"],
            f"{len(config['commands'])} command{len(config['commands']) > 1 and 's' or ''}"
        )

        for name, command in config.get("commands", {}).items():
            il.cprint(
                f"* aos {config['name'].lower()} {name}\n└→    {command['help']}",
                34
            )


if "--nobox" not in argv:
    il.box(85, "Administer AOS", f"v{var.version}")

try:
    _ = argv[1]
except IndexError:
    help_command()
    raise AOSError("A command is required. Showing help command.")

match argv[1]:
    # Built-ins:
    case "help":
        help_command()

        raise AOSError("")
    case _:
        pass


# Plugins, start by loading always-enabled plugins
plugin_list = Plugin.get_plugins(True)

for plugin in dict.keys(plugin_list):
    Plugin.load_plugin(plugin, "")

# change the list to have unloaded plugins
plugin_list = Plugin.get_plugins(False)

if len(argv) < 3: raise AOSError("[x] more arguments are required for plugin commands\n└→ run AOS help for commands")

for config in plugin_list.values():
    if argv[1].lower() == config["name"].lower():
        for name, command in config.get("commands", {}).items():
            if argv[2].lower() == name:
                Plugin.load_plugin(config["name"].lower(), name)

if AOS.app is not None:
    AOS.run_server()

