from typing import Literal
from common.app.modules.tts.providers.base import TTSBaseProvider
from common.app.modules.tts.providers.google import GoogleProvider


class TTSProvider:
    @staticmethod
    def get_provider(provider: str) -> TTSBaseProvider:
        if provider == "google":
            return GoogleProvider()
        raise ValueError(f"Unsupported provider: {provider}")

    @classmethod
    async def generate_audio(
        cls,
        text: str,
        voice: TTSBaseProvider.TTSVoice,
        audio_config: TTSBaseProvider.TTSAudioConfig,
        provider: Literal["google"] = "google",
    ) -> str:
        tts_provider = TTSProvider.get_provider(provider)
        return await tts_provider.tts(text, voice, audio_config)
