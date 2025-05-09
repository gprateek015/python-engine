import uuid
from apps.www.app.models.api.requests.story import GenerateStoryRequest
from common.app.modules.llm.functions.story.generate.llm_component import (
    generate_story_llm_component,
)
from common.app.modules.llm.functions.story.models import (
    GenerateStoryOutputModel,
    GenerateStoryParamsModel,
)
from common.app.modules.tts.providers import TTSProvider
from common.app.modules.tts.providers.base import TTSBaseProvider
from common.app.modules.tts.providers.smallest_ai import SmallestAITTSProvider
from common.core.s3 import async_s3_client


class StoryService:
    @classmethod
    async def generate_story(
        cls,
        data: GenerateStoryRequest,
    ):
        story_text = await generate_story_llm_component.run(
            params=GenerateStoryParamsModel(
                theme=data.theme,
                language=data.language,
                genre=data.genre,
                target_length=data.target_length,
                story_idea=data.story_idea,
                tone=data.tone,
            ),
        )
        assert isinstance(story_text, GenerateStoryOutputModel)

        voice_name = "emily"
        voice_language_code = "en"

        if data.language == "hindi":
            voice_name = "ronald"
            voice_language_code = "hi"

        audio_content = await TTSProvider.generate_audio(
            text=story_text.story,
            voice=SmallestAITTSProvider.TTSVoice(
                language_code=voice_language_code,
                voice_id=voice_name,
                model="lightning",
            ),
            audio_config=TTSBaseProvider.TTSAudioConfig(),
            provider="smallest_ai",
        )

        key = f"stories/{uuid.uuid4()}.wav"

        await async_s3_client.put_object(
            Bucket="taletalk",
            Key=key,
            Body=audio_content,
        )

        url = await async_s3_client.get_s3_url(Bucket="taletalk", Key=key)

        return url
