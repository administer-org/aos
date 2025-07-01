# pyxfluff 2025

from pydantic import BaseModel
from typing import Dict, List, Any, Optional


class Ratelimiting(BaseModel):
    max_reqs: int
    reset_timeframe: int
    max_incidents_before_block: int


class Banner(BaseModel):
    color: str
    text: str

class MongoAuth(BaseModel):
    use_auth: bool
    username: str
    password: str


class MongoConfig(BaseModel):
    use_prod_db: bool
    address: str
    auth: Optional[MongoAuth]
    timeout_ms: int


class SecurityConfig(BaseModel):
    ratelimiting: Ratelimiting
    use_roblox_lock: bool = False
    use_api_keys: bool = False
    use_sessions: bool = False

class Plausible(BaseModel):
    use_plausible: bool = False
    data_url: str
    site_url: str


class CoreConfig(BaseModel):
    instance_name: str

    is_dev: bool
    logging_location: str
    enable_bot_execution: bool

    node: str
    can_be_home_node: bool

    plausible: Plausible

    extra_plugins: Optional[List[str]] = []

    banner: Banner
    report_webhook_url: str

    flags: Dict[str, Any] = {}
    dbattrs: MongoConfig
    security: SecurityConfig
