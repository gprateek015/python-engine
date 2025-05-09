from typing import List, Literal, Optional
import httpx
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

from common.app.modules.llm.promtps import LLMPromptItem
from common.app.modules.llm.providers.base import LLMBaseProvider


class OpenRouterProvider(LLMBaseProvider):
    provider: Literal["openrouter"] = "openrouter"

    def _convert_to_message_params(
        self, prompt: List[LLMPromptItem]
    ) -> List[ChatCompletionMessageParam]:
        messages: List[ChatCompletionMessageParam] = []
        for message in prompt:
            if message.role == "user":
                messages.append(
                    ChatCompletionUserMessageParam(role="user", content=message.content)
                )
            elif message.role == "assistant":
                messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=message.content
                    )
                )
            else:
                raise ValueError(f"Unsupported role: {message.role}")
        return messages

    async def get_chat_completion(
        self,
        model: str,
        prompt: List[LLMPromptItem],
        provider: Optional[dict],
        reasoning: Optional[dict],
        usage: Optional[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[dict[str, float]] = None,
        top_logprobs: Optional[int] = None,
        min_p: Optional[float] = None,
        top_a: Optional[float] = None,
    ):
        api_key = self.get_api_key()

        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            http_client=httpx.AsyncClient(),
        )

        messages = self._convert_to_message_params(prompt)

        completion = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return completion.choices[0].message.content
