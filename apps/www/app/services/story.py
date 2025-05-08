from apps.www.app.models.api.requests.story import GenerateStoryRequest
from common.app.modules.llm.functions.story.generate.llm_component import (
    generate_story_llm_component,
)
from common.app.modules.llm.functions.story.models import GenerateStoryParamsModel


class StoryService:
    @classmethod
    async def generate_story(
        cls,
        data: GenerateStoryRequest,
    ):
        return await generate_story_llm_component.run(
            params=GenerateStoryParamsModel(
                theme=data.theme,
                language=data.language,
                genre=data.genre,
                target_length=data.target_length,
                story_idea=data.story_idea,
                tone=data.tone,
            ),
        )
