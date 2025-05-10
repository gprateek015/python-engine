import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from apps.www.app.models.api.requests.story import GenerateStoryRequest
from apps.www.app.models.api.responses.story import GenerateStoryResponse
from apps.www.app.services.story import StoryService
from common.core.config import config

router = APIRouter(
    prefix=config.SERVICE_ROUTE_PREFIX + "/story",
)


@router.post("/")
async def generate_story(data: GenerateStoryRequest):
    story_text, url = await StoryService.generate_story(data)
    return GenerateStoryResponse(story=story_text, audio_url=url)

@router.post("/sse")
async def generate_story_sse(request: GenerateStoryRequest):
    async def event_stream():
        async for event, data in StoryService.generate_story_sse(request):
            yield f"data: {json.dumps({'event': event, 'text': data})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")