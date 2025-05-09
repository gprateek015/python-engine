import inspect
from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, List, Literal, Optional, Type, Union


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

        async def execute(
            self,
            step_input: Any,
            params: "LLMFunction.ParamsModel",
        ) -> Optional[str]:
            prompt: List[LLMPromptItem] = []
            if self.extend_prompt is not None:
                if inspect.iscoroutinefunction(self.extend_prompt):
                    prompt = await self.extend_prompt(step_input, params)
                else:
                    prompt = self.extend_prompt(step_input, params)

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
    output_model: Optional[Type[OutputModel]] = Field(None, description="Output model")

    async def run(
        self,
        params: ParamsModel,
    ) -> Union[OutputModel, Any]:
        intermediate_outputs: List[Any] = []
        for step in self.steps:
            step_output: Optional[Dict[str, Any]] = None
            step_input = (
                intermediate_outputs[-1] if len(intermediate_outputs) > 0 else params
            )

            if isinstance(step, LLMFunction.TransformStep):
                step_output = step.execute(step_input)
                intermediate_outputs.append(step_output)

            elif isinstance(step, LLMFunction.CompletionStep):
                completion = await step.execute(step_input, params)
                intermediate_outputs.append(completion)

        if self.output_model is not None:
            return self.output_model.model_validate(intermediate_outputs[-1])
        else:
            return intermediate_outputs[-1]
