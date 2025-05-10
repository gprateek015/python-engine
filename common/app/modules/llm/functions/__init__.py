import inspect
from pydantic import BaseModel, Field
from typing import Any, AsyncGenerator, AsyncIterator, Callable, Dict, List, Literal, Optional, Type, Union, overload, Coroutine


from common.app.modules.llm.promtps import LLMPromptItem
from common.app.modules.llm.providers import LLMProvider


class LLMFunction(BaseModel):
    class ParamsModel(BaseModel):
        pass

    class OutputModel(BaseModel):
        pass

    class Step(BaseModel):
        type: Literal["transform", "completion"]

    class TransformStep(Step):
        type: Literal["transform"] = "transform"
        function: Callable[[Any], Dict[str, Any]]

        def execute(self, step_input: Any) -> Dict[str, Any]:
            return self.function(step_input)

    class CompletionStep(Step):
        type: Literal["completion"] = "completion"
        model: str
        extend_prompt: Optional[
            Callable[[Any, "LLMFunction.ParamsModel"], List[LLMPromptItem]]
        ] = None
        max_tokens: Optional[int] = None
        temperature: Optional[float] = None

        @overload
        async def execute(
            self,
            step_input: Any,
            params: "LLMFunction.ParamsModel",
            stream: Literal[False] = False,
        ) -> Optional[str]: ...
        
        @overload
        async def execute(
            self,
            step_input: Any,
            params: "LLMFunction.ParamsModel",
            stream: Literal[True] = True,
        ) -> AsyncGenerator[str, None]: 
            pass

        async def execute(
            self,
            step_input: Any,
            params: "LLMFunction.ParamsModel",
            stream: bool = False,
        ) -> Union[Optional[str], AsyncGenerator[str, None]]:
            prompt: List[LLMPromptItem] = []
            if self.extend_prompt is not None:
                if inspect.iscoroutinefunction(self.extend_prompt):
                    prompt = await self.extend_prompt(step_input, params)
                else:   
                    prompt = self.extend_prompt(step_input, params)

            if stream:
                return await LLMProvider.get_chat_completion_with_streaming(
                    model=self.model,
                    prompt=prompt,
                    provider=None,
                    reasoning=None,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            else:
                return await LLMProvider.get_chat_completion(
                    model=self.model,
                    prompt=prompt,
                    provider=None,
                    reasoning=None,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    
                )

    name: str = Field(..., title="Name", description="Name of the function")
    steps: List[Union[TransformStep, CompletionStep]] = Field(
        [], description="Steps to execute"
    )
    params_model: Type[ParamsModel] = Field(..., description="Parameters model")
    output_model: Optional[Type[OutputModel]] = Field(default=None, description="Output model")
    stream: bool = Field(default=False, description="Stream the output - only the last completion step can be streamed")

    async def _stream_last_completion(self, step: CompletionStep, step_input: Any, params: ParamsModel) -> AsyncGenerator[str, None]:
        async for chunk in await step.execute(step_input, params, stream=True):
            if chunk is not None:
                yield chunk
    
    async def run(
        self,
        params: ParamsModel,
    ) -> Union[OutputModel, Any, AsyncGenerator[str, None]]:
        intermediate_outputs: List[Any] = []
        # Check if stream is True, the last step must be a completion step
        if self.stream and not isinstance(self.steps[-1], LLMFunction.CompletionStep):
            raise ValueError("Last step must be a completion step when stream is True")
        
        for index, step in enumerate(self.steps):
            step_output: Optional[Dict[str, Any]] = None
            step_input = (
                intermediate_outputs[-1] if len(intermediate_outputs) > 0 else params
            )

            if isinstance(step, LLMFunction.TransformStep):
                step_output = step.execute(step_input)
                intermediate_outputs.append(step_output)

            elif isinstance(step, LLMFunction.CompletionStep):
                if self.stream and index == len(self.steps) - 1:
                    return self._stream_last_completion(step, step_input, params)
                
                completion = await step.execute(step_input, params)
                
                if completion is not None:
                    intermediate_outputs.append(completion)

        if self.output_model is not None:
            return self.output_model.model_validate(intermediate_outputs[-1])
        else:
            return intermediate_outputs[-1]