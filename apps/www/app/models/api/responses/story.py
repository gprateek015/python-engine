from typing import Literal
from pydantic import BaseModel


class GenerateStoryResponse(BaseModel):
    url: str
    success: Literal["ok"] = "ok"
