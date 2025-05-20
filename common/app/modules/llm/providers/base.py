from typing import AsyncGenerator, AsyncIterator, Literal, Optional, Union, overload

from pydantic import BaseModel
from common.app.modules.llm.promtps import LLMPromptItem
from common.core.config import config


class LLMBaseProvider(BaseModel):
    provider: Literal["openrouter", "gemini"]

    def get_api_key(self) -> str:
        # Get all api keys using the provider
        api_key: Optional[str] = None
        if self.provider == "openrouter":
            api_key = config.OPENROUTER_API_KEY
        elif self.provider == "gemini":
            api_key = config.GEMINI_API_KEY

        if not api_key:
            raise Exception("API key not found")

        return api_key

    async def get_chat_completion(
        self,
        model: str,
        prompt: list[LLMPromptItem],
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
    ) -> Optional[str]: ...
    
    async def get_chat_completion_with_streaming(
        self,
        model: str,
        prompt: list[LLMPromptItem],
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
    ) -> AsyncGenerator[str, None]: ...
