from typing import Literal, Optional
from pydantic import BaseModel


class GenerateStoryRequest(BaseModel):
    genre: str
    target_length: str
    theme: str
    tone: str
    language: Literal["english", "hindi"] = "english"
    story_idea: Optional[str]
