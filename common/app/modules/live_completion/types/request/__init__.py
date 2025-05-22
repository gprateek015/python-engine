from typing import Any, Literal, Optional, Union
from av import AudioFrame, frame
from pydantic import BaseModel


class BaseMessageRequest(BaseModel):
    turn_complete: Optional[bool] = False
    role: Literal["user"] = "user"


class TextMessageRequest(BaseMessageRequest):
    type: Literal["text"] = "text"
    text: str


class AudioMessageRequest(BaseMessageRequest):
    type: Literal["audio"] = "audio"
    audio_frame: Any


MessageRequest = Union[TextMessageRequest, AudioMessageRequest]
