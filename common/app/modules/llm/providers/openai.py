from openai import OpenAI

from common.app.modules.llm.providers.base import BaseProvider

client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v1"})


class OpenAIProvider(BaseProvider):
    def __init__(self):
        super().__init__(provider="openai")

    def get_chat_completion(self):
        api_key = self.get_api_key()
        pass
