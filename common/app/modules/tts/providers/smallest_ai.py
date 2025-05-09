import re
from smallestai.waves import AsyncWavesClient

from typing import AsyncIterator, List, Literal
from common.app.modules.tts.providers.base import TTSBaseProvider
import aiohttp


def chunk_text(text: str, chunk_size: int = 250) -> List[str]:
    SENTENCE_END_REGEX = re.compile(r".*[-.—!?,;:…।|]$")
    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text.strip())
            break

        chunk_text = text[:chunk_size]
        last_break_index = -1

        # Find last sentence boundary using regex
        for i in range(len(chunk_text) - 1, -1, -1):
            if SENTENCE_END_REGEX.match(chunk_text[: i + 1]):
                last_break_index = i
                break

        if last_break_index == -1:
            # Fallback to space if no sentence boundary found
            last_space = chunk_text.rfind(" ")
            if last_space != -1:
                last_break_index = last_space
            else:
                last_break_index = chunk_size - 1

        chunks.append(text[: last_break_index + 1].strip())
        text = text[last_break_index + 1 :].strip()

    return chunks


class SmallestAITTSProvider(TTSBaseProvider):
    provider: Literal["smallest_ai"] = "smallest_ai"

    class TTSVoice(TTSBaseProvider.TTSVoice):
        model: Literal["lightning", "lightning-large"] = "lightning"
        language_code: Literal["en", "hi", "ta", "fr", "de", "pl"] = "en"

    # async def tts(
    #     self,
    #     text: str,
    #     voice: TTSVoice,
    #     audio_config: TTSBaseProvider.TTSAudioConfig,
    # ) -> bytes:
    #     waves_client = AsyncWavesClient(api_key=self.get_api_key())
    #     audio_content = await waves_client.synthesize(
    #         text=text,
    #     )
    #     # If stream is True, then audio_content is an iterator
    #     # If save_as is provided, then audio_content is None
    #     # Otherwise, audio_content is bytes
    #     assert isinstance(audio_content, bytes)
    #     return audio_content

    async def tts_stream(
        self,
        text: str,
        voice: TTSVoice,
        audio_config: TTSBaseProvider.TTSAudioConfig,
    ) -> AsyncIterator[bytes]:
        async with aiohttp.ClientSession() as session:
            url = f"https://waves-api.smallest.ai/api/v1/{voice.model}/get_speech"
            chunk_size = 250
            if voice.model == "lightning-large":
                chunk_size = 140
            chunks = chunk_text(text, chunk_size)

            async def audio_stream():
                for chunk in chunks:
                    payload = {
                        "text": chunk,
                        "sample_rate": voice.sample_rate,
                        "voice_id": voice.voice_id,
                        "add_wav_header": True,
                        "speed": voice.speed,
                        "model": voice.model,
                    }

                    if voice.model == "lightning-large":
                        if voice.consistency is not None:
                            payload["consistency"] = voice.consistency
                        if voice.similarity is not None:
                            payload["similarity"] = voice.similarity
                        if voice.enhancement is not None:
                            payload["enhancement"] = voice.enhancement

                    headers = {
                        "Authorization": f"Bearer {self.get_api_key()}",
                        "Content-Type": "application/json",
                    }

                    async with session.post(
                        url=url, json=payload, headers=headers
                    ) as res:
                        if res.status != 200:
                            raise Exception(
                                f"Failed to synthesize speech: {await res.text()}. For more information, visit https://waves.smallest.ai/"
                            )

                        yield await res.read()

        return audio_stream()

    async def tts(
        self,
        text: str,
        voice: TTSVoice,
        audio_config: TTSBaseProvider.TTSAudioConfig,
    ) -> bytes:
        audio_content = b""
        async for chunk in await self.tts_stream(text, voice, audio_config):
            audio_content += chunk
        return audio_content
