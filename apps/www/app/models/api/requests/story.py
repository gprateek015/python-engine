from typing import Optional
from pydantic import BaseModel


class GenerateStoryRequest(BaseModel):
    genre: str
    target_length: str
    theme: str
    tone: str
    language: str
    story_idea: Optional[str]
