# Will pick the provider
# Expose get_chat_completion and get_chat_completion_stream


from typing import AsyncGenerator, AsyncIterator, Literal, Optional, Union, overload

from common.app.modules.llm.promtps import LLMPromptItem
from common.app.modules.llm.providers.base import LLMBaseProvider
from common.app.modules.llm.providers.open_router import OpenRouterProvider


class LLMProvider:
    def __init__(self, provider: str):
        self.provider = provider

    @staticmethod
    def get_provider(model: str) -> LLMBaseProvider:
        return OpenRouterProvider()

    @classmethod
    async def get_chat_completion(
        cls,
        model: str,
        prompt: list[LLMPromptItem],
        provider: Optional[dict],
        reasoning: Optional[dict],
        usage: Optional[dict] = None,
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
        llm_provider = LLMProvider.get_provider(model)
        return await llm_provider.get_chat_completion(
            model,
            prompt,
            provider,
            reasoning,
            usage,
            max_tokens,
            temperature,
            seed,
            top_p,
            top_k,
            frequency_penalty,
            presence_penalty,
            repetition_penalty,
            logit_bias,
            top_logprobs,
            min_p,
            top_a,
        )
    
    @classmethod
    async def get_chat_completion_with_streaming(
        cls,
        model: str,
        prompt: list[LLMPromptItem],
        provider: Optional[dict],
        reasoning: Optional[dict],
        usage: Optional[dict] = None,
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
        llm_provider = LLMProvider.get_provider(model)
        return llm_provider.get_chat_completion_with_streaming(
            model,
            prompt,
            provider,
            reasoning,
            usage,
            max_tokens,
            temperature,
            seed,
            top_p,
            top_k,
            frequency_penalty,
            presence_penalty,
            repetition_penalty,
            logit_bias,
            top_logprobs,
            min_p,
            top_a,
        )
    