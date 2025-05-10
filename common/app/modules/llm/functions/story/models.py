from typing import Literal, Optional


from common.app.modules.llm.functions import LLMFunction


class GenerateStoryParamsModel(LLMFunction.ParamsModel):
    genre: str
    theme: str
    language: Optional[Literal["english", "hindi"]] = "english"
    target_length: Optional[Literal["1000_words", "2500_words", "4000_words"]] = "1000_words"
    story_idea: Optional[str] = None
    tone: Optional[str] = None


class GenerateStoryOutputModel(LLMFunction.OutputModel):
    story: str
