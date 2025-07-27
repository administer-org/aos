# pyxfluff 2025

from time import time

from fastapi import APIRouter

class AdminFrontend():
    def __init__(self, app):
        self.app = app
        self.startup_time = time()
        self.router = APIRouter()

    def mount(self):
        @self.router.get("/test")
        def test_admin():
            print("OK")
