import asyncio
from typing import Optional, Tuple
from apps.www.app.services.character.character import CharacterService
from common.app.modules.live_completion.providers.gemini import LiveGeminiProvider
from common.app.modules.live_completion.types.request import TextMessageRequest
from common.app.modules.live_completion.types.response import MessageResponse
from common.core.config import config
from fastapi import APIRouter, Request

router = APIRouter(
    prefix=config.SERVICE_ROUTE_PREFIX + "/character",
)


@router.get("/test")
async def get_character():
    provider = LiveGeminiProvider(
        config={
            "model": "gemini-2.0-flash-live-001",
            "temperature": 0.5,
            "max_tokens": 20000,
            "modality": "TEXT",
        }
    )

    try:
        message_queue = asyncio.Queue[Tuple[str | Tuple[bytes, str], Optional[bool]]](
            maxsize=10
        )

        async def on_message(message: MessageResponse):
            if message.type == "text":
                print(message.text)
            else:
                print(message.audio, message.mime_type)

        # connect_task = asyncio.create_task(provider.connect(message_queue, on_message)

        await provider.on("message", on_message)

        await asyncio.sleep(2)
        await provider.send(TextMessageRequest(text="Tell me a joke"))
        await asyncio.sleep(2)
        await provider.send(
            TextMessageRequest(text="Or wait tell me two jokes.", turn_complete=True)
        )
        await provider.close()

        await asyncio.sleep(15)

        return {"message": "Character created"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await provider.close()


@router.post("/offer")
async def offer(request: Request):
    response = await CharacterService.offer(request)
    return response
