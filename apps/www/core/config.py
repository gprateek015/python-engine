import os
import sys
from typing import Dict

from dotenv import load_dotenv, find_dotenv

env_path = find_dotenv()
if env_path and env_path != "":
    load_dotenv()


class Config:
    SERVICE_ROUTE_PREFIX: str = "/www"
    PORT: int = 8000
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")


class LocalConfig(Config):
    HOT_RELOAD: bool = True


class DevelopmentConfig(Config):
    HOT_RELOAD: bool = False


class ProductionConfig(Config):
    HOT_RELOAD: bool = False


def get_config():
    env = str(os.getenv("ENVIRONMENT", "local"))
    if "local" in env:
        env = "local"
    config_type: Dict[str, Config] = {
        "local": LocalConfig(),
        "development": DevelopmentConfig(),
        "production": ProductionConfig(),
    }
    return config_type[env]


config = get_config()
