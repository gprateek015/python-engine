from openai import OpenAI

from common.app.modules.llm.models.providers.base import BaseProvider

client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v1"})

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    def get_chat_completion(self):
        api_key = self.get_api_key()
        pass
