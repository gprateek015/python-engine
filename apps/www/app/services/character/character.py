from apps.www.app.services.character.web_call import AudioCallServer


class CharacterService:
    @classmethod
    async def offer(cls, request):
        service = AudioCallServer()
        return await service.offer(request)
