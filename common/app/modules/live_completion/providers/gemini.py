import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Awaitable, Callable, Literal, Optional, Tuple

from pydantic import BaseModel
from common.app.modules.live_completion.providers.base import LiveCompletionProvider
from google.genai import types, live
from google.genai.live import types as live_types
from google import genai

class LiveGeminiProvider(LiveCompletionProvider):
    class GeminiVoiceConfig(BaseModel):
        language_code: str
        voice_id: str

    provider: Literal["gemini"] = "gemini"
    # session: live.AsyncSession | None = None

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[live.AsyncSession]:
        if self.session:
            yield self.session
            return

        gemini_modalities = []
        if self.config.get("modality", None) == "TEXT":
            gemini_modalities.append(types.Modality.TEXT)
        elif self.config.get("modality", None) == "IMAGE":
            gemini_modalities.append(types.Modality.IMAGE)
        elif self.config.get("modality", None) == "AUDIO":
            gemini_modalities.append(types.Modality.AUDIO)

        generation_config=types.GenerationConfig(
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
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self.config.get("voice_config", None).get("voice_id", None)),
                ),
                language_code=self.config.get("voice_config", None).get("language_code", None),
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
            async with client.aio.live.connect(model=self.config.get("model", "gemini-2.0-flash-live-001"), config=config) as session:
                self.session = session
                yield self.session
        finally:
            if self.session:
                await self.session.close()
                self.session = None


    async def send_message(
        self,
        message_queue: asyncio.Queue[Tuple[str | Tuple[bytes, str], Optional[bool]]], # Tuple[bytes, str] is (audio, mime_type)
    ):
        """
        Send a message to the Gemini session.

        @params:
            message_queue: asyncio.Queue[Tuple[str | Tuple[bytes, str], Optional[bool]]]
                - Tuple[str | Tuple[bytes, str] -> message
                - Optional[bool] -> turn_complete
        """
        while True:
            try:
                message, turn_complete = await asyncio.wait_for(message_queue.get(), timeout=3)
                if isinstance(message, str):
                    await self.session.send_client_content(
                        turns={"role": "user", "parts": [{"text": message}]}, turn_complete=turn_complete
                    )
                elif isinstance(message, tuple) and len(message) == 2:
                    await self.session.send_client_content(
                        turns={"role": "user", "parts": [{"inline_data": types.Blob(data=message[0], mime_type=message[1])}]}, turn_complete=turn_complete
                    )
                
                if turn_complete:
                    break
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in send_message: {e}")
                raise e


    async def listen_for_response(self, on_message: Callable[[str | Tuple[bytes, str]], Awaitable[None]]):
        async with self.get_session() as session:
            try:
                async for message in session.receive():
                    if message.server_content and message.server_content.model_turn and message.server_content.model_turn.parts:
                        for part in message.server_content.model_turn.parts:
                            if part.text:
                                await on_message(part.text)
                            elif part.inline_data:
                                if part.inline_data.data and part.inline_data.mime_type:
                                    await on_message((part.inline_data.data, part.inline_data.mime_type))
                    if message.server_content and message.server_content.turn_complete:
                        return
            except Exception as e:
                print(f"Error in listen_for_response: {e}")
                raise

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def connect(self, message_queue: asyncio.Queue[Tuple[str | Tuple[bytes, str], Optional[bool]]], on_message: Callable[[str | Tuple[bytes, str]], Awaitable[None]]):
        async with self.get_session() as session, asyncio.TaskGroup() as task_group:
            send_message_task = task_group.create_task(self.send_message(message_queue))
            task_group.create_task(self.listen_for_response(on_message))

            # We wait for the send_message task to complete before closing the session
            # Since it's wrapped in a task group, before exit it will wait for all the tasks in the group to complete
            await send_message_task

