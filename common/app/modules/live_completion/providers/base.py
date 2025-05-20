from typing import Any, Literal, Optional, Union
from pydantic import BaseModel
from google.genai import live

from common.core.config import config

class LiveCompletionProvider(BaseModel):
    provider: Literal["gemini"] = "gemini"
    config: dict
    session: Any = None

    def get_api_key(self):
        if self.provider == "gemini":
            return config.GEMINI_API_KEY

        raise ValueError(f"Provider {self.provider} not supported")

    def get_provider(self):
        return self.provider

    def get_client(self): ...
