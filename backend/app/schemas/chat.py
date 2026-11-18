"""Wire contract with the frontend.

Mirrors frontend/src/features/chat/types.ts. Fields are snake_case in Python and
camelCase on the wire (conversationId, followUp, delayMs).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel

ChatMode = Literal["bot", "agent"]
StepSender = Literal["bot", "agent", "system"]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatRequest(CamelModel):
    conversation_id: str
    mode: ChatMode
    intent: str | None = None
    text: str | None = None

    @model_validator(mode="after")
    def _intent_or_text(self) -> "ChatRequest":
        if not self.intent and not self.text:
            raise ValueError("Either 'intent' or 'text' is required")
        return self


class BotStep(CamelModel):
    sender: StepSender
    text: str
    author: str | None = None


class QuickReply(CamelModel):
    label: str
    intent: str


class FollowUp(CamelModel):
    intent: str
    delay_ms: int


class ChatTurn(CamelModel):
    steps: list[BotStep]
    replies: list[QuickReply] = []
    mode: ChatMode | None = None
    follow_up: FollowUp | None = None
