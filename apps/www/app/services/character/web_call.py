# server.py
import asyncio
import json
import time
from typing import Optional, Tuple
from aiohttp import web
from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription
from aiortc.rtcrtpreceiver import RemoteStreamTrack
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling
from aiortc.contrib.media import MediaRecorder
from av import AudioFrame
from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions, ListenWebSocketClient, LiveTranscriptionEvents, AsyncListenWebSocketClient, ListenWebSocketOptions
from common.app.modules.live_completion.providers.gemini import LiveGeminiProvider
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
        self.audio = bytearray()
        self.connect_task: asyncio.Task | None = None

    async def offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

        self.pc = RTCPeerConnection(
            configuration=RTCConfiguration(
                iceServers=[
                    RTCIceServer(
                        urls=["stun:stun.l.google.com:19302"]
                    )
                ]
            )
        )

        async def get_audio_track():
        # Implement audio track retrieval logic here
            pass

        def on_ice_connection_state_change():
            if self.pc is not None:
                print('ICE connection state is %s' % self.pc.iceConnectionState)
        
        async def handle_audio_frame(pcm_bytes, sample_rate, channels):
            # Here you can send pcm_bytes to a STT engine (e.g., Vosk, Whisper, Google STT)
            print(f"Received audio frame with {len(pcm_bytes)} bytes")
            self.audio.extend(pcm_bytes)

        # recorder = MediaRecorder('output.wav')
        async def on_track(track: RemoteStreamTrack):
            print(f"Track received: {track.kind}")
            
            api_key = config.DEEPGRAM_API_KEY
            if api_key is None:
                raise ValueError("DEEPGRAM_API_KEY is not set")

            deepgram = DeepgramClient(api_key)
            dg_connection = deepgram.listen.asyncwebsocket.v("1")

            provider = LiveGeminiProvider(config={
                "model": "gemini-2.0-flash-live-001",
                "temperature": 0.5,
                "max_tokens": 20000,
                "modality": "TEXT",
            })

            async def on_ai_response(message: str | Tuple[bytes, str]):
                if isinstance(message, str):
                    print(f"AI response: {message}")
                else:
                    print(message[1], message[0])

            message_queue = asyncio.Queue[Tuple[str | Tuple[bytes, str], Optional[bool]]](maxsize=10)

            self.connect_task = asyncio.create_task(provider.connect(message_queue, on_ai_response))

            assert isinstance(dg_connection, AsyncListenWebSocketClient)
            
            @track.on("ended")
            async def on_track_ended():
                await dg_connection.finish()

            async def on_open(self, open, **kwargs):
                print(f"\n\n{open}\n\n")

            async def on_message(selff, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) == 0:
                    return
                print(f"speaker: {sentence}")
                if self.connect_task is None:
                    while not message_queue.empty():
                        await message_queue.get()
                    self.connect_task = asyncio.create_task(provider.connect(message_queue, on_ai_response))
                await message_queue.put((sentence, None))

            async def on_utterance_end(selff, utterance_end, **kwargs):
                print(f"\n\n{utterance_end}\n\n")
                await message_queue.put(("", True))
                await asyncio.sleep(1)
                if self.connect_task is not None:
                    await self.connect_task
                    self.connect_task = None

            async def on_error(self, error, **kwargs):
                print(f"\n\n{error}\n\n")

            async def on_close(self, close, **kwargs):
                print(f"\n\n{close}\n\n")

            dg_connection.on(LiveTranscriptionEvents.Open, on_open) # type: ignore
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message) # type: ignore
            dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end) # type: ignore
            dg_connection.on(LiveTranscriptionEvents.Error, on_error) # type: ignore
            dg_connection.on(LiveTranscriptionEvents.Close, on_close) # type: ignore

            # Get the first frame to determine sample rate and channels
            try:
                first_frame = await asyncio.wait_for(track.recv(), timeout=2)
                assert isinstance(first_frame, AudioFrame)
                sample_rate = first_frame.rate
                channels = len(first_frame.layout.channels)  # Convert tuple length to integer
                
                options: ListenWebSocketOptions = ListenWebSocketOptions(
                    model="nova-3",
                    punctuate=True,
                    language="en-US",
                    encoding="linear16",
                    channels=channels,
                    sample_rate=sample_rate,
                    ## To get UtteranceEnd, the following must be set:
                    interim_results=True,
                    utterance_end_ms="2000",
                    vad_events=True,
                )

                await dg_connection.start(options)
                
                # Send the first frame
                if first_frame.format.name == "s16":
                    pcm_bytes = first_frame.to_ndarray().tobytes()
                    await dg_connection.send(pcm_bytes)
            except asyncio.TimeoutError:
                print("Failed to get first audio frame")
                return

            while True:
                try:
                    frame = await asyncio.wait_for(track.recv(), timeout=2)
                    assert isinstance(frame, AudioFrame)
                    
                    if frame.format.name != "s16":
                        print(f"Unsupported format: {frame.format.name}")
                        continue

                    pcm_bytes = frame.to_ndarray().tobytes()
                    await dg_connection.send(pcm_bytes)

                except asyncio.TimeoutError:
                    print("Audio track recv timed out")
                    continue
                
                except Exception as e:
                    print(f"Error: {e}")
                    break

            
                
        self.pc.on('iceconnectionstatechange', on_ice_connection_state_change)
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
                    with open("audio.wav", "wb") as f:
                        wav_file = wave.open(f, 'wb')
                        wav_file.setnchannels(2)  # Stereo
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(48000)  # 48kHz sample rate
                        wav_file.writeframes(self.audio)
                        wav_file.close()

        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        return {
            'sdp': self.pc.localDescription.sdp,
            'type': self.pc.localDescription.type
        }

   