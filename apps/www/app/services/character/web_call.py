# server.py
import asyncio
import json
import time
from typing import Optional, Tuple
from aiohttp import web
from aiortc import (
    RTCConfiguration,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.rtcrtpreceiver import RemoteStreamTrack
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling
from aiortc.contrib.media import MediaRecorder
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
from common.app.modules.live_completion.providers.gemini import LiveGeminiProvider
from common.app.modules.live_completion.types.request import (
    AudioMessageRequest,
    TextMessageRequest,
)
from common.app.modules.live_completion.types.response import MessageResponse
from common.app.modules.stt.providers.deepgram import LiveDeepgramSTTProvider
from common.core.config import config
import numpy as np
import wave
import av

from aiortc import MediaStreamTrack
from aiortc.contrib.media import MediaBlackhole
import asyncio


class AudioCallServer:
    def __init__(self):
        self.pc: RTCPeerConnection | None = None

    async def offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        self.pc = RTCPeerConnection(
            configuration=RTCConfiguration(
                iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
            )
        )

        async def get_audio_track():
            # Implement audio track retrieval logic here
            pass

        def on_ice_connection_state_change():
            if self.pc is not None:
                print("ICE connection state is %s" % self.pc.iceConnectionState)

        # recorder = MediaRecorder('output.wav')
        async def on_track(track: RemoteStreamTrack):
            print(f"Track received: {track.kind}")

            gemini_config = {
                "model": "gemini-2.0-flash-live-001",
                "temperature": 0.5,
                "max_tokens": 20000,
                "modality": "TEXT",  # "AUDIO",
                # "voice_config": {
                #     "language_code": "en-IN",
                #     "voice_id": "Puck",  # Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr
                # },
            }
            async with LiveDeepgramSTTProvider.start() as stt_provider, LiveGeminiProvider.start(
                gemini_config
            ) as llm_provider:

                async def on_ai_response(message: MessageResponse):
                    if message.type == "text":
                        print(f"AI response: {message.text}")
                    else:
                        print(f"AI response: {message.audio}")

                await llm_provider.on("message", on_ai_response)

                async def on_open(self, open, **kwargs):
                    print(f"\n\n{open}\n\n")

                async def on_message(self, result, **kwargs):
                    sentence = result.channel.alternatives[0].transcript
                    if len(sentence) == 0:
                        return
                    print(f"speaker: {sentence}")
                    await llm_provider.send(TextMessageRequest(text=sentence))

                async def on_utterance_end(self, utterance_end, **kwargs):
                    print(f"\n\n{utterance_end}\n\n")
                    await llm_provider.send(
                        TextMessageRequest(text="", turn_complete=True)
                    )
                    # await llm_provider.close()

                async def on_error(self, error, **kwargs):
                    print(f"\n\n{error}\n\n")

                async def on_close(self, close, **kwargs):
                    print(f"\n\n{close}\n\n")

                # Event handler for when the track ends
                track.on("ended", stt_provider.close)
                # Event handler for when the STT
                stt_provider.on(LiveTranscriptionEvents.Open, on_open)  # type: ignore
                stt_provider.on(LiveTranscriptionEvents.Transcript, on_message)  # type: ignore
                stt_provider.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)  # type: ignore
                stt_provider.on(LiveTranscriptionEvents.Error, on_error)  # type: ignore
                stt_provider.on(LiveTranscriptionEvents.Close, on_close)  # type: ignore

                while True:
                    try:
                        frame = await asyncio.wait_for(track.recv(), timeout=2)
                        assert isinstance(frame, AudioFrame)

                        # await stt_provider.send(frame)
                        await llm_provider.send(AudioMessageRequest(audio_frame=frame))

                    except asyncio.TimeoutError:
                        print("Audio track recv timed out")
                        continue

                    except Exception as e:
                        raise e

        self.pc.on("iceconnectionstatechange", on_ice_connection_state_change)
        # Add audio track
        # self.pc.addTrack(await self.get_audio_track())
        self.pc.on("track", on_track)

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            if self.pc is not None:
                print("Connection state is %s", self.pc.connectionState)
                if self.pc.connectionState == "failed":
                    await self.pc.close()
                if self.pc.connectionState == "closed":
                    pass

        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        return {
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type,
        }
