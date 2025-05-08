from typing import Optional


from common.app.modules.llm.functions import LLMFunction


class GenerateStoryParamsModel(LLMFunction.ParamsModel):
    genre: str
    target_length: str
    theme: str
    language: str
    story_idea: Optional[str] = None
    tone: Optional[str] = None


class GenerateStoryOutputModel(LLMFunction.OutputModel):
    story: str
