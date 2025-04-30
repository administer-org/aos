# pyxfluff 2024-2025

from pydantic import BaseModel


class RatingPayload(BaseModel):
    vote: int
    is_favorite: bool
