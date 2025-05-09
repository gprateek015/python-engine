from fastapi import APIRouter

from apps.www.app.models.api.requests.story import GenerateStoryRequest
from apps.www.app.models.api.responses.story import GenerateStoryResponse
from apps.www.app.services.story import StoryService
from common.core.config import config

router = APIRouter(
    prefix=config.SERVICE_ROUTE_PREFIX + "/story",
)


@router.post("/")
async def generate_story(data: GenerateStoryRequest):
    url = await StoryService.generate_story(data)
    return GenerateStoryResponse(url=url)
