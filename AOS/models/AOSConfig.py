# pyxfluff 2025

from pydantic import BaseModel
from typing import Dict, Any, List

class State(BaseModel):
    requests: int
    votes_today: int
    default_app: Dict[Any, Any]
    downloads_today: int

    permitted_versions: List[str]
    unchecked_endpoints: List[str]

class AOSConfig(BaseModel):
    version: str

    default_port: int
    default_host: str

    workers: int

    plugin_load_order: List[str]

    state: State
