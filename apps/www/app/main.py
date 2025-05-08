from fastapi import FastAPI

# import routers
from apps.www.app.routers.system import router as system_router
from apps.www.app.routers.story import router as story_router

app = FastAPI()


app.include_router(system_router)
app.include_router(story_router)
