"""Conversation logic. Replace the placeholder replies with real intent handling / RAG."""

from app.schemas.chat import BotStep, ChatRequest, ChatTurn, QuickReply

START_REPLIES = [
    QuickReply(label="Check my coverage", intent="coverage"),
    QuickReply(label="What's my deductible?", intent="deductible"),
    QuickReply(label="Talk to a person", intent="agent"),
]


def respond(request: ChatRequest) -> ChatTurn:
    if request.intent == "start":
        return ChatTurn(
            steps=[BotStep(sender="bot", text="Hi! I can help with your health insurance plan.")],
            replies=START_REPLIES,
        )

    # TODO: route intents, call app.rag for free-text questions.
    user_input = request.text or request.intent
    return ChatTurn(
        steps=[BotStep(sender="bot", text=f"(backend placeholder) You said: {user_input}")],
        replies=START_REPLIES,
    )
