from typing import Literal, Optional, Union
from pydantic import BaseModel


class BaseMessageResponse(BaseModel):
    turn_complete: Optional[bool] = False
    role: Literal["assistant"] = "assistant"


class TextMessageResponse(BaseMessageResponse):
    type: Literal["text"] = "text"
    text: str


class AudioMessageResponse(BaseMessageResponse):
    type: Literal["audio"] = "audio"
    audio: bytes
    mime_type: str


MessageResponse = Union[TextMessageResponse, AudioMessageResponse]
