from typing import AsyncIterator, Literal, Optional, Union
from pydantic import BaseModel

from common.core.config import config

TTSProviderLiteral = Literal["smallest_ai"]


class TTSBaseProvider(BaseModel):
    provider: TTSProviderLiteral = "smallest_ai"

    class TTSVoice(BaseModel):
        language_code: str
        voice_id: str
        model: Optional[str] = None
        gender: Optional[Literal["male", "female", "neutral"]] = "male"
        speed: Optional[float] = 1.0
        consistency: Optional[float] = 0.5
        similarity: Optional[float] = 0.0
        enhancement: Optional[int] = 1
        sample_rate: Optional[int] = 24000

    class TTSAudioConfig(BaseModel):
        audio_encoding: Literal[
            "LINEAR16", "MP3", "OGG_OPUS", "MULAW", "ALAW", "PCM"
        ] = "MP3"

    def get_api_key(self) -> str:
        api_key: Optional[str] = None

        if self.provider == "smallest_ai":
            api_key = config.SMALLEST_AI_API_KEY

        if not api_key:
            raise Exception("API key not found")

        return api_key

    async def tts(
        self,
        text: str,
        voice: TTSVoice,
        audio_config: TTSAudioConfig,
    ) -> bytes: ...

    async def tts_stream(
        self,
        text: str,
        voice: TTSVoice,
        audio_config: TTSAudioConfig,
    ) -> AsyncIterator[bytes]: ...
