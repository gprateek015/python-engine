from fastapi import FastAPI

# import routers
from apps.www.app.routers.system import router as system_router
from apps.www.app.routers.story import router as story_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(system_router)
app.include_router(story_router)
