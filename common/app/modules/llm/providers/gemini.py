from typing import AsyncGenerator, AsyncIterator, List, Literal, Optional, Union
from google import genai
from google.genai import types
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from pydantic import BaseModel

from common.app.modules.llm.promtps import LLMPromptItem
from common.app.modules.llm.providers.base import LLMBaseProvider


class GeminiProvider(LLMBaseProvider):
    provider: Literal["gemini"] = "gemini"

    def _convert_to_message_format(
        self, prompt: List[LLMPromptItem]
    ) -> types.ContentListUnion:
        messages: types.ContentListUnion = []
        for message in prompt:
            if message.role == "user":
                messages.append(
                    types.Content(role="user", parts=[types.Part(text=message.content)])
                )
            elif message.role == "assistant":
                messages.append(
                    types.Content(role="assistant", parts=[types.Part(text=message.content)])
                )
            else:
                continue
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
    ) -> Optional[str]:
        api_key = self.get_api_key()

        client = genai.Client(api_key=api_key)
        messages = self._convert_to_message_format(prompt)

        system_prompt = ""
        response_schema=None

        response = await client.aio.models.generate_content(
            model=model,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                response_schema=response_schema,
                seed=seed,
            )
        )
        return response.text
    
    async def get_chat_completion_with_streaming(
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
    ) -> AsyncGenerator[str, None]:
        api_key = self.get_api_key()

        client = genai.Client(api_key=api_key)

        system_prompt = ""
        response_schema=None

        messages = self._convert_to_message_format(prompt)

        async for chunk in await client.aio.models.generate_content_stream(
            contents=messages,
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                response_schema=response_schema,
                seed=seed,
            )
        ):
            if chunk.text is not None:
                yield chunk.text