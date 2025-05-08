import sys
from fastapi import APIRouter

from common.app.modules.llm.models.providers.open_router import OpenRouterProvider
from common.core.config import config

router = APIRouter(
    prefix=config.SERVICE_ROUTE_PREFIX + "/system",
)


@router.get("/health/")
async def health():
    privider = OpenRouterProvider()
    print(privider.get_chat_completion())
    return {"status": "ok"}
