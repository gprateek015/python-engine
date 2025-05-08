from typing import Literal, Optional
from common.core.config import config

class BaseProvider:
    provider: Literal["openai", "openrouter"]

    def __init__(self, provider: Literal["openai", "openrouter"]):
        self.provider = provider

    def get_api_key(self) -> str:
        # Get all api keys using the provider
        api_key: Optional[str] = None
        if self.provider == "openai":
            api_key = config.OPENAI_API_KEY
        elif self.provider == "openrouter":
            api_key = config.OPENROUTER_API_KEY
        
        if not api_key:
            raise Exception("API key not found")
        
        return api_key
