# pyxfluff 2025

import importlib.util

from .frontend import Frontend
from .backend import BackendAPI
from .public import PublicAPI

from ..admin import AdminRoutes, AdminFrontend

from AOS import globals, app
from time import sleep

import AOS.plugin_loader as plugin_loader
from AOS.deps import il

while app is None:
    sleep()  # wait for fastapi

# Load required dependencies
for plugin in ["middleware"]:
    plugin_loader.load_plugin(plugin, "")


backend_api = BackendAPI(app)
public_api = PublicAPI(app)

backend_api.initialize_api_routes()
backend_api.initialize_content_routes()
public_api.initialize_routes()

app.include_router(backend_api.router, prefix="/api")
app.include_router(backend_api.asset_router, prefix="/api")
app.include_router(public_api.router, prefix="/pub")

# Mount Admin API if we are installed with the `server` optional

if importlib.util.find_spec("bcrypt"):
    admin_frontend = AdminFrontend(app)
    admin_api = AdminRoutes(app)

    admin_frontend.mount()
    admin_api.mount_api()

    app.include_router(admin_frontend.router, prefix="/a")
    app.include_router(admin_api.router, prefix="/admin")
else:
    il.cprint("[!] You did not install with `uv pip install .[server], we can't serve the admin interface!", 31)



frontend = Frontend(app)
frontend.initialize_frontend()
