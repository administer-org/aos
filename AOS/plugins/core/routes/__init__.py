# pyxfluff 2025

import AOS.plugin_loader
from .frontend import Frontend
from .backend import BackendAPI
from .public import PublicAPI
from AOS import globals, app
from time import sleep

import AOS

while app is None:
    sleep(0)  # wait for fastapi

# Load required dependencies
for plugin in ["middleware"]:
#for plugin in []:
    AOS.plugin_loader.load_plugin(plugin, "")


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
