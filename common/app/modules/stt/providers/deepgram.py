from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Awaitable, Callable
from common.app.modules.stt.providers.base import BaseSTTProvider
from av import AudioFrame
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    LiveOptions,
    ListenWebSocketClient,
    LiveTranscriptionEvents,
    AsyncListenWebSocketClient,
    ListenWebSocketOptions,
)


class LiveDeepgramSTTProvider(BaseSTTProvider):
    _connection: AsyncListenWebSocketClient | None = None

    def on(
        self, event: LiveTranscriptionEvents, callback: Callable[[Any], Awaitable[None]]
    ):
        assert self._connection is not None
        self._connection.on(event, callback)

    @asynccontextmanager
    @staticmethod
    async def start():
        stt_provider = LiveDeepgramSTTProvider()
        api_key = stt_provider.get_api_key()

        deepgram = DeepgramClient(api_key)
        dg_connection = deepgram.listen.asyncwebsocket.v("1")
        assert isinstance(dg_connection, AsyncListenWebSocketClient)

        stt_provider._connection = dg_connection

        try:
            yield stt_provider
        finally:
            await stt_provider.close()

    async def send(self, audio_frame: AudioFrame):
        if self._connection is None:
            raise Exception("STT connection not started")

        # Update the options with the new sample rate and channels
        sample_rate = audio_frame.rate
        self.options["sample_rate"] = sample_rate
        channels = len(audio_frame.layout.channels)
        self.options["channels"] = channels

        if not await self._connection.is_connected():
            deepgram_options: ListenWebSocketOptions = ListenWebSocketOptions(
                model="nova-3",
                punctuate=True,
                language=self.options.get("language", "en-US"),
                encoding=self.options.get("encoding", "linear16"),
                channels=self.options.get("channels", 1),
                sample_rate=self.options.get("sample_rate", 16000),
                ## To get UtteranceEnd, the following must be set:
                interim_results=True,
                utterance_end_ms=self.options.get("utterance_end_ms", "2000"),
                vad_events=True,
            )
            await self._connection.start(options=deepgram_options)

        pcm_bytes = audio_frame.to_ndarray().tobytes()

        await self._connection.send(pcm_bytes)

    async def close(self):
        if self._connection is not None:
            await self._connection.finish()
            self._connection = None
