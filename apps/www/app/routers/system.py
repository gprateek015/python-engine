from fastapi import APIRouter

from common.core.config import config

router = APIRouter(
    prefix=config.SERVICE_ROUTE_PREFIX + "/system",
)


@router.get("/health/")
async def health():
    return {"status": "ok"}
