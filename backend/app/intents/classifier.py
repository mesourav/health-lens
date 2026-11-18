"""Works out WHAT the customer is asking. Input is redacted text; output is an intent label.

The model never sees policy data — only the (redacted) question.
"""

import re
from dataclasses import dataclass
from typing import Literal

from app.llm.ollama import LLMUnavailable, chat_json

Intent = Literal[
    "deductible_status",  # personal: how much deductible / out-of-pocket is used or left
    "coverage_check",  # personal: is <service> covered on MY plan, what does it cost
    "claim_status",  # personal: my claims, bills, what I owe
    "premium_due",  # personal: my premium amount, due date, autopay
    "policy_summary",  # personal: my plan name, status, overview
    "general_question",  # general: how insurance/plan rules work (answered from docs via RAG)
    "handoff",  # wants a human
    "greeting",  # hi / thanks / menu
    "unknown",
]
INTENTS: tuple[str, ...] = Intent.__args__  # type: ignore[attr-defined]
PERSONAL_INTENTS = {
    "deductible_status",
    "coverage_check",
    "claim_status",
    "premium_due",
    "policy_summary",
}


@dataclass
class Classification:
    intent: Intent
    service: str | None = None  # for coverage_check, e.g. "MRI"
    source: Literal["llm", "keywords"] = "llm"


_SYSTEM = """Classify a health insurance member's chat message. Reply with JSON only.

Intents:
- deductible_status: how much of THEIR deductible or out-of-pocket maximum is used or left
- coverage_check: whether a specific service/treatment is covered for THEM or what it costs them
  (set "service" to the service name, e.g. "MRI", "therapy", "physical therapy")
- claim_status: THEIR claims, bills, what they owe for a past visit
- premium_due: THEIR monthly premium, payment, due date, autopay
- policy_summary: THEIR plan name, policy status, or a general overview of their policy
- general_question: how insurance or plan rules work in general (e.g. what is prior approval,
  do I need a referral, what counts toward a deductible, how do appeals work)
- handoff: wants to talk to a human, agent, or person
- greeting: hello, thanks, or asking what you can do
- unknown: anything else

Personal details are replaced with placeholders like [NAME] or [DATE]; ignore them."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": list(INTENTS)},
        "service": {"type": ["string", "null"]},
    },
    "required": ["intent", "service"],
}


async def classify(redacted_text: str) -> Classification:
    try:
        data = await chat_json(_SYSTEM, redacted_text, _SCHEMA)
        intent = data.get("intent")
        if intent in INTENTS:
            return Classification(intent, data.get("service") or None, "llm")
    except LLMUnavailable:
        pass
    return classify_keywords(redacted_text)


# --- Fallback when the model is unavailable (also keeps tests model-free) ---
_RULES: list[tuple[re.Pattern[str], Intent]] = [
    (re.compile(r"\b(person|human|agent|someone|representative)\b", re.I), "handoff"),
    (re.compile(r"\b(referral|prior|approval|network|appeal|emergency|telehealth)", re.I), "general_question"),
    (re.compile(r"\b(deductible|out[- ]of[- ]pocket|left|remaining)\b", re.I), "deductible_status"),
    (re.compile(r"\b(claims?|bill|billed|owe|eob)\b", re.I), "claim_status"),
    (re.compile(r"\b(premium|payment|pay|autopay|due)\b", re.I), "premium_due"),
    (re.compile(r"\b(covered|coverage|cover|cost|copay|mri|scan|therap)", re.I), "coverage_check"),
    (re.compile(r"\b(my plan|my policy|summary|overview)\b", re.I), "policy_summary"),
    (re.compile(r"\b(what is|what's|how do|how does|how long|explain|meaning)\b", re.I), "general_question"),
    (re.compile(r"^\s*(hi|hello|hey|thanks|thank you|menu|help)\b", re.I), "greeting"),
]


def classify_keywords(text: str) -> Classification:
    for pattern, intent in _RULES:
        if pattern.search(text):
            return Classification(intent, None, "keywords")
    return Classification("unknown", None, "keywords")
