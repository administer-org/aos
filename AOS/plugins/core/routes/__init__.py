# pyxfluff 2025

from .frontend import Frontend
from .backend import BackendAPI
from .public import PublicAPI

from ..admin import AdminRoutes, AdminFrontend

from AOS import globals, app
from time import sleep

import AOS.plugin_loader
import AOS

while app is None:
    sleep(0)  # wait for fastapi

# Load required dependencies
for plugin in ["middleware"]:
    AOS.plugin_loader.load_plugin(plugin, "")


backend_api = BackendAPI(app)
public_api = PublicAPI(app)

backend_api.initialize_api_routes()
backend_api.initialize_content_routes()
public_api.initialize_routes()

app.include_router(backend_api.router, prefix="/api")
app.include_router(backend_api.asset_router, prefix="/api")
app.include_router(public_api.router, prefix="/pub")

# Mount Admin API

admin_api = AdminRoutes(app)
admin_frontend = AdminFrontend(app)

admin_api.mount_api()
admin_frontend.mount()

app.include_router(admin_api.router, prefix="/admin")
app.include_router(admin_frontend.router, prefix="/a")

frontend = Frontend(app)
frontend.initialize_frontend()
