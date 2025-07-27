# pyxfluff 2025

from time import time

from fastapi import APIRouter

class AdminRoutes():
    def __init__(self, app):
        self.app = app
        self.startup_time = time()
        self.router = APIRouter()

    def mount_api(self):
        @self.router.get("/test")
        def test_admin():
            print("OK")
