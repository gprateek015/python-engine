import asyncio
from contextlib import asynccontextmanager
import wave
from scipy.signal import resample
import numpy as np
import ffmpeg
import subprocess
import io

from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
)

from av import AudioFrame
from pydantic import BaseModel
from websockets import ConnectionClosedOK
from common.app.modules.live_completion.providers.base import LiveCompletionProvider
from google.genai import types, live
from google.genai.live import types as live_types
from google import genai

from common.app.modules.live_completion.types.request import MessageRequest
from common.app.modules.live_completion.types.response import (
    AudioMessageResponse,
    MessageResponse,
    TextMessageResponse,
)


class LiveGeminiProvider(LiveCompletionProvider):
    class GeminiVoiceConfig(BaseModel):
        language_code: str
        voice_id: str

    provider: Literal["gemini"] = "gemini"
    _event_handlers: Dict[
        Literal["message"], List[Callable[[MessageResponse], Awaitable[None]]]
    ] = {}
    turns: List[types.Content] = []
    audio_bytes: Any = None

    @asynccontextmanager
    @staticmethod
    async def start(config: Dict[str, Any]):
        provider = LiveGeminiProvider(config=config)
        asyncio.create_task(provider._start_session())
        try:
            yield provider
        finally:
            await provider.close()
            provider._event_handlers = {}
            provider.turns = []

    @staticmethod
    def _convert_audio_frame_to_pcm_bytes(audio_frame: AudioFrame):
        # Use ffmpeg to convert the audio frame to PCM bytes
        pass

    async def on(
        self,
        event: Literal["message"],
        callback: Callable[[MessageResponse], Awaitable[None]],
    ):
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(callback)

    async def send(
        self,
        message: MessageRequest,
    ):
        if self.session is None:
            asyncio.create_task(self._start_session())

        # Wait for the session to be started with a timeout of 5 seconds
        start_time = asyncio.get_event_loop().time()
        while self.session is None:
            if asyncio.get_event_loop().time() - start_time > 5:
                raise Exception("Live Gemini connection not started")
            await asyncio.sleep(0.1)

        assert isinstance(self.session, live.AsyncSession)
        try:
            if message.type == "text":
                current_turn = types.Content(
                    role="user", parts=[types.Part(text=message.text)]
                )
                self.turns.append(current_turn)
                await self.session.send_client_content(
                    turns=[current_turn],
                    turn_complete=message.turn_complete or False,
                )
            elif message.type == "audio":
                audio_bytes = self._convert_audio_frame_to_pcm_bytes(
                    message.audio_frame
                )
                if self.audio_bytes is None:
                    self.audio_bytes = bytearray()
                self.audio_bytes.extend(audio_bytes)
                current_turn = types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                data=audio_bytes, mime_type="audio/pcm;rate=16000"
                            )
                        )
                    ],
                )
                self.turns.append(current_turn)
                # await self.session.send_client_content(
                #     turns=[current_turn],
                #     turn_complete=message.turn_complete or False,
                # )
                await self.session.send_realtime_input(
                    audio=types.Blob(
                        data=audio_bytes,
                        mime_type="audio/pcm;rate=16000",
                    )
                )
        except Exception as e:
            print(f"Error in send: {e}")
            raise e

    async def _listen_for_response(self):
        try:
            if self.session is None:
                print("Gemini session not started")
                return

            assert isinstance(self.session, live.AsyncSession)
            async for message in self.session.receive():
                if (
                    message.server_content
                    and message.server_content.model_turn
                    and message.server_content.model_turn.parts
                ):
                    for part in message.server_content.model_turn.parts:
                        response = None
                        if part.text:
                            response = TextMessageResponse(
                                type="text",
                                text=part.text,
                                turn_complete=message.server_content.turn_complete,
                            )
                        elif part.inline_data:
                            if part.inline_data.data and part.inline_data.mime_type:
                                response = AudioMessageResponse(
                                    type="audio",
                                    audio=part.inline_data.data,
                                    mime_type=part.inline_data.mime_type,
                                    turn_complete=message.server_content.turn_complete,
                                )

                        self.turns.append(types.Content(role="assistant", parts=[part]))
                        if response is not None:
                            for handler in self._event_handlers.get("message", []):
                                await handler(response)
                if message.server_content and message.server_content.turn_complete:
                    # Start the new session for the next turn
                    asyncio.create_task(self._start_session())
                    return
        except ConnectionClosedOK:
            return
        except Exception as e:
            print(f"Error in listen_for_response: {e}")
            raise

    async def close(self):
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                print(f"Error in close: {e}")
            self.session = None

    async def _start_session(self):
        gemini_modalities = []
        if self.config.get("modality", None) == "TEXT":
            gemini_modalities.append(types.Modality.TEXT)
        elif self.config.get("modality", None) == "IMAGE":
            gemini_modalities.append(types.Modality.IMAGE)
        elif self.config.get("modality", None) == "AUDIO":
            gemini_modalities.append(types.Modality.AUDIO)

        generation_config = types.GenerationConfig(
            temperature=self.config.get("temperature", None),
            max_output_tokens=self.config.get("max_tokens", None),
            top_p=self.config.get("top_p", None),
            top_k=self.config.get("top_k", None),
            response_schema=self.config.get("response_schema", None),
        )

        speech_config = None
        if self.config.get("voice_config", None):
            speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.config.get("voice_config", None).get(
                            "voice_id", None
                        )
                    ),
                ),
                language_code=self.config.get("voice_config", None).get(
                    "language_code", None
                ),
            )

        config = types.LiveConnectConfig(
            media_resolution=self.config.get("media_resolution", None),
            seed=self.config.get("seed", None),
            system_instruction=self.config.get("system_prompt", None),
            speech_config=speech_config,
            response_modalities=gemini_modalities,
            generation_config=generation_config,
        )

        client = genai.Client(api_key=self.get_api_key())

        try:
            async with client.aio.live.connect(
                model=self.config.get("model", "gemini-2.0-flash-live-001"),
                config=config,
            ) as session, asyncio.TaskGroup() as task_group:
                self.session = session
                # Set the initial context
                # await self.session.send_client_content(
                #     turns=self.turns,
                #     turn_complete=False,
                # )
                listening_task = task_group.create_task(self._listen_for_response())

                while True:
                    # Check if the session is closed
                    if self.session is None or listening_task.done():
                        break
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in _start_session: {e}")
            raise e
        finally:
            await self.close()
            with open("output.wav", "wb") as f:
                wav_file = wave.open(f, "wb")
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)
                wav_file.writeframes(self.audio_bytes)
                wav_file.close()
