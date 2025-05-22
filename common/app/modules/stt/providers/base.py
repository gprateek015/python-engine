from pydantic import BaseModel
from typing import AsyncIterator, Literal
from common.core.config import config


class BaseSTTProvider(BaseModel):
    provider: Literal["deepgram"] = "deepgram"
    options: dict = {}

    def get_api_key(self) -> str:
        if self.provider == "deepgram":
            api_key = config.DEEPGRAM_API_KEY
        if api_key is None:
            raise ValueError(f"Provider {self.provider} not supported")
        return api_key

    async def transcribe_live(self, audio_stream: AsyncIterator[bytes]):
        pass

    async def transcribe_file(self, audio_file: str):
        pass
