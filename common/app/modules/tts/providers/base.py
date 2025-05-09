from typing import Literal, Optional
from pydantic import BaseModel

from common.core.config import config


class TTSBaseProvider(BaseModel):
    provider: Literal["google"] = "google"

    class TTSVoice(BaseModel):
        language_code: str
        name: str
        voice_clone: Optional[dict] = None
        gender: Optional[Literal["male", "female", "neutral"]] = "male"

    class TTSAudioConfig(BaseModel):
        audio_encoding: Literal[
            "LINEAR16", "MP3", "OGG_OPUS", "MULAW", "ALAW", "PCM"
        ] = "MP3"

    def get_api_key(self) -> str:
        api_key: Optional[str] = None

        if self.provider == "google":
            api_key = config.GOOGLE_API_KEY

        if not api_key:
            raise Exception("API key not found")

        return api_key

    async def tts(
        self, text: str, voice: TTSVoice, audio_config: TTSAudioConfig
    ) -> str: ...
