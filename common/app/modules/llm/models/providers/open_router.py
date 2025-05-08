import httpx
from openai import OpenAI

from common.app.modules.llm.models.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    def __init__(self):
        super().__init__(provider="openrouter")

    def get_chat_completion(self):
        api_key = self.get_api_key()

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            http_client=httpx.Client(),
        )

        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[{"role": "user", "content": "What is the meaning of life?"}],
        )
        return completion.choices[0].message.content


if __name__ == "__main__":
    provider = OpenRouterProvider()
    print(provider.get_chat_completion())
