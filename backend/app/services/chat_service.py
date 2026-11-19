"""Conversation engine: login → redact → classify → (tool | RAG | handoff) → reply.

`session` is the signed cookie dict from SessionMiddleware. It holds login state only.
"""

import re
from datetime import date, datetime
from typing import Any

from app.intents import replies as R
from app.intents import tools
from app.intents.classifier import PERSONAL_INTENTS, Classification, classify
from app.intents.scope import SUPPORTED_LINES, out_of_scope_line
from app.policy.repository import get_policy, verify
from app.privacy.redact import redact
from app.rag.answer import answer_general
from app.schemas.chat import BotStep, ChatRequest, ChatTurn, FollowUp, QuickReply

Session = dict[str, Any]

MAX_LOGIN_ATTEMPTS = 3
AGENT_NAME = "Sam · Member advocate"
_POLICY_NO = re.compile(r"\b[A-Z]{2}-?\s?\d{6}\b", re.IGNORECASE)
_DOB_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y")


def _bot(text: str, replies: list | None = None) -> ChatTurn:
    return ChatTurn(steps=[BotStep(sender="bot", text=text)], replies=replies or [])


# ---------------------------------------------------------------- entry point
async def respond(req: ChatRequest, session: Session) -> ChatTurn:
    # A new conversation (e.g. "restart") starts logged out — handy for demos.
    if session.get("cid") != req.conversation_id:
        session.clear()
        session["cid"] = req.conversation_id

    if req.intent:
        return await _handle_intent(req.intent, session)
    if req.mode == "agent":
        return ChatTurn(
            steps=[
                BotStep(
                    sender="agent",
                    author=AGENT_NAME,
                    text="Got it. Let me pull up your account so I can look into that. One moment.",
                )
            ],
        )
    return await _handle_text(req.text or "", session)


# ---------------------------------------------------------------- quick replies
_TAP_TO_INTENT = {
    "deductible": Classification("deductible_status"),
    "claims": Classification("claim_status"),
    "premium": Classification("premium_due"),
    "summary": Classification("policy_summary"),
    "mri": Classification("coverage_check", "MRI"),
    "therapy": Classification("coverage_check", "therapy"),
    "raise_claim": Classification("raise_claim"),
}


async def _handle_intent(intent: str, session: Session) -> ChatTurn:
    if intent == "start":
        session["stage"] = "await_policy"
        return _bot(
            "Hi! I'm the Health Lens assistant. I can answer questions about your coverage, "
            "costs and claims, or connect you with a person.\n\n"
            "To look up your plan, please type your policy number (it looks like HL-123456). "
            "Or tap a general question below.",
            R.BEFORE_LOGIN,
        )
    if intent == "menu":
        return _bot("Happy to help. What else is on your mind?", _main_replies(session))
    if intent in R.GENERAL_QUESTIONS:
        return await _general(R.GENERAL_QUESTIONS[intent], session)
    if intent in _TAP_TO_INTENT:
        return await _dispatch(_TAP_TO_INTENT[intent], session, original_text=None)
    if handoff := _handoff_flow(intent, session):
        return handoff
    return _fallback(session)


# ---------------------------------------------------------------- typed messages
async def _handle_text(text: str, session: Session) -> ChatTurn:
    if session.get("stage") == "await_dob":
        return _check_dob(text, session)

    if not _is_authed(session) and (match := _POLICY_NO.search(text)):
        session["pending_policy"] = match.group(0)
        session["stage"] = "await_dob"
        return _bot("Thanks. For security, please type your date of birth (for example 1990-01-31).")

    if line := out_of_scope_line(text):
        supported = ", ".join(SUPPORTED_LINES[:-1]) + " and " + SUPPORTED_LINES[-1]
        return _bot(
            f"Sorry, I can only help with {supported} insurance, so I can't help with {line} insurance here. "
            "A member advocate can point you to the right team.",
            [R.MORE, R.PERSON],
        )

    names = [get_policy(session["policy_id"])["first_name"]] if _is_authed(session) else []
    safe_text = redact(text, names)  # ← only this redacted text is ever sent to the model
    classification = await classify(safe_text)
    return await _dispatch(classification, session, original_text=safe_text)


def _check_dob(text: str, session: Session) -> ChatTurn:
    dob = _parse_date(text)
    if dob is None:
        return _bot("Sorry, I couldn't read that date. Please use the format YYYY-MM-DD, e.g. 1990-01-31.")

    policy_id = verify(session.get("pending_policy", ""), dob)
    session.pop("pending_policy", None)
    if policy_id is None:
        session["attempts"] = session.get("attempts", 0) + 1
        session["stage"] = "await_policy"
        if session["attempts"] >= MAX_LOGIN_ATTEMPTS:
            session["stage"] = "locked"
            return _bot(
                "Those details still don't match our records, so I've paused sign-in for your "
                "security. A member advocate can help you.",
                [R.PERSON],
            )
        # Same message whether the policy number or the DOB was wrong (don't leak which).
        return _bot("Those details don't match our records. Please type your policy number again.")

    session.update(stage="authed", policy_id=policy_id, attempts=0)
    first_name = get_policy(policy_id)["first_name"]
    return _bot(f"Thanks, {first_name}, you're verified. What would you like to know?", R.MAIN)


def _parse_date(text: str) -> date | None:
    value = text.strip()
    for fmt in _DOB_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- routing
async def _dispatch(c: Classification, session: Session, original_text: str | None) -> ChatTurn:
    if c.intent in PERSONAL_INTENTS:
        if not _is_authed(session):
            return _ask_login(session)
        policy = get_policy(session["policy_id"])  # always the logged-in customer's own policy
        if c.intent == "deductible_status":
            return tools.deductible_status(policy)
        if c.intent == "claim_status":
            return tools.claim_status(policy)
        if c.intent == "premium_due":
            return tools.premium_due(policy)
        if c.intent == "policy_summary":
            return tools.policy_summary(policy)
        if c.intent == "riders":
            return tools.riders(policy)
        if c.intent == "waiting_period":
            return tools.waiting_periods(policy)
        if c.intent == "coverage_check":
            turn = tools.coverage_check(policy, c.service, original_text)
            if turn:
                return turn
            # Service not in our coverage table → maybe the plan documents mention it.

    if c.intent == "raise_claim":
        policy = get_policy(session["policy_id"]) if _is_authed(session) else None
        return tools.raise_claim(original_text, policy)
    if c.intent == "handoff":
        return _handoff_flow("handoff", session)  # type: ignore[return-value]
    if c.intent == "greeting":
        return _bot("Hi there! Here are some things I can help with.", _main_replies(session))

    # general_question, unknown, or unmatched coverage → search the plan documents.
    if original_text:
        return await _general(original_text, session)
    return _fallback(session)


async def _general(question: str, session: Session) -> ChatTurn:
    answer = await answer_general(question)
    if answer is None:
        return _fallback(session)
    text = f"{answer.text}\n\nSource: {'; '.join(answer.sources)}"
    return _bot(text, [R.MORE, R.PERSON])


def _ask_login(session: Session) -> ChatTurn:
    if session.get("stage") == "locked":
        return _bot("Sign-in is paused for your security. A member advocate can help you.", [R.PERSON])
    session["stage"] = "await_policy"
    return _bot(
        "I can look that up once you're verified. Please type your policy number (it looks like HL-123456).",
        R.BEFORE_LOGIN,
    )


def _fallback(session: Session) -> ChatTurn:
    return _bot(
        "Hmm, I'm not sure about that one. I can help with any of these, or connect you with a person.",
        _main_replies(session),
    )


def _main_replies(session: Session) -> list:
    return R.MAIN if _is_authed(session) else [*R.BEFORE_LOGIN, R.PERSON]


def _is_authed(session: Session) -> bool:
    return session.get("stage") == "authed" and "policy_id" in session


# ---------------------------------------------------------------- human handoff (scripted)
def _handoff_flow(intent: str, session: Session) -> ChatTurn | None:
    name = get_policy(session["policy_id"])["first_name"] if _is_authed(session) else "there"
    if intent == "handoff":
        return _bot(
            "Of course. What's it about? That way I can send you to the right person.",
            [
                QuickReply(label="A bill or claim", intent="queue"),
                QuickReply(label="My coverage", intent="queue"),
                QuickReply(label="Something else", intent="queue"),
            ],
        )
    if intent == "queue":
        return ChatTurn(
            steps=[
                BotStep(
                    sender="bot",
                    text="Thanks. I'm passing our chat to a member advocate so you "
                    "won't have to repeat yourself. The wait right now is about 3 minutes.",
                ),
                BotStep(sender="system", text="You're #2 in line"),
            ],
            replies=[QuickReply(label="Call me back instead", intent="callback")],
            follow_up=FollowUp(intent="agentJoin", delay_ms=4000),
        )
    if intent == "agentJoin":
        return ChatTurn(
            steps=[
                BotStep(sender="system", text="Sam joined the chat"),
                BotStep(
                    sender="agent",
                    author=AGENT_NAME,
                    text=f"Hi {name}, I'm Sam. I've read through your chat. What can I help you sort out?",
                ),
            ],
            mode="agent",
        )
    if intent == "callback":
        return _bot(
            "All set. Sam will call you at the phone number on your policy within the next "
            "2 hours. You can close this window.",
            [R.MORE],
        )
    return None
