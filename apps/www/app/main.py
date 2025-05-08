from fastapi import FastAPI

# import routers
from apps.www.app.routers.system import router as system_router

app = FastAPI()


app.include_router(system_router)