# pyxfluff 2025


from AOS import globals, AOSError

import AOS

import il
import orjson
import importlib

from pathlib import Path


def get_plugins(only_include_autoload):
    plugins = {}
    order = globals.plugin_load_order

    # load autoload plugins anyways
    for plugin in order:
        config = orjson.loads(
            (Path("AOS/plugins") / plugin / "meta.json").read_text())
        plugins[plugin] = config

        if not only_include_autoload:
            for plugin in Path("AOS/plugins").iterdir():
                if plugin.name == "__pycache__": continue

                config = orjson.loads(
                    (plugin / "meta.json").read_text()
                )
                plugins[plugin] = config

    return plugins


def load_plugin(plugin, command):
    try:
        config = orjson.loads(
            (Path("AOS/plugins") / plugin / "meta.json").read_text())
    except FileNotFoundError:
        raise AOSError(
            f"Plugin AOS/plugins/{plugin} does not have a valid meta.json file.")

    il.cprint(f"[-] Loading plugin {plugin} ({config['name']})", 33)

    if config["requires_fastapi"]:
        if AOS.app is None:
            AOS.load_fastapi_app()

    if config.get("init", False):
        importlib.import_module(f".plugins.{plugin}", package="AOS")

    try:
        importlib.import_module(
            f".plugins.{plugin}.{
                config.get('commands', {})[command]['directory']}",
            package="AOS")
    except KeyError:
        if command is None or command == "":
            return

        il.cprint(f"[x] Invalid command for plugin {plugin}", 31)
    except Exception as e:
        raise AOSError(f"Failed to load plugin: {e}")
