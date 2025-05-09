import aiohttp
from typing import Literal
from common.app.modules.tts.providers.base import TTSBaseProvider

from common.core.config import config


class GoogleProvider(TTSBaseProvider):
    provider: Literal["google"] = "google"

    @staticmethod
    def _get_project_id() -> str:
        project_id = config.GOOGLE_PROJECT_ID
        if not project_id:
            raise Exception("GOOGLE_PROJECT_ID is not set")
        return project_id

    async def tts2(
        self,
        text: str,
        voice: TTSBaseProvider.TTSVoice,
        audio_config: TTSBaseProvider.TTSAudioConfig,
    ) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://texttospeech.googleapis.com/v1/text:synthesize",
                headers={
                    "Authorization": f"Bearer {self.get_api_key()}",
                    "X-Goog-User-Project": GoogleProvider._get_project_id(),
                },
                json={
                    "input": {"markup": text},
                    "voice": {
                        "languageCode": voice.language_code,
                        "name": voice.name,
                        "voiceClone": voice.voice_clone,
                    },
                    "audioConfig": {"audioEncoding": audio_config.audio_encoding},
                },
            ) as response:
                response_json = await response.json()
                if response.status != 200:
                    raise Exception(f"Failed to synthesize text: {response_json}")
                return response_json["audioContent"]
