# pyxfluff 2025

from AOS.plugins.database import db
from AOS import AOSError

from . import queue

_queue = queue.action_queue

class APIController():
    def __init__(self, guild_id: int):
        data = db.get(guild_id, db.BOT_STORE)

        if data is None:
            raise AOSError("You need to initialize with `/link` before running moderation commands.", False)
        
        self.place_id = data["place_id"]
        self.api_url = data["api_url"]
        self.api_token = data["api_token"]

    def ban(self, data):
        existing_queue = _queue.get(self.place_id)

        if existing_queue is None:
            _queue[self.place_id] = []
            existing_queue = _queue[self.place_id]

        data["action_type"] = "ban"

        existing_queue.append(data)

        
