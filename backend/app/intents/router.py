"""Semantic router: picks the intent whose example sentences are closest in meaning to the question.

Uses our own embedding model (no chat model needed), so it is fast and reliable even with a
small model on a laptop. Only redacted customer text is embedded — never policy data.
To teach it a new phrasing, add an example sentence below.
"""

import math

from app.llm.ollama import embed

EXAMPLES: dict[str, list[str]] = {
    "deductible_status": [
        "how much of my deductible is left",
        "how much deductible have I paid so far",
        "have I met my deductible yet",
        "how much do I still have to pay before insurance starts paying",
        "how much is left on my out-of-pocket maximum",
        "how close am I to my out of pocket max",
    ],
    "coverage_check": [
        "is an MRI covered",
        "does my plan cover therapy",
        "is physical therapy covered for me",
        "how much will a specialist visit cost me",
        "will my insurance pay for an x-ray",
        "is botox covered",
        "what is my copay for mental health visits",
    ],
    "claim_status": [
        "show my recent claims",
        "what is the status of my claim",
        "how much do I owe for my last visit",
        "was my MRI claim approved",
        "show me my medical bills",
        "has my claim been paid",
        "did you pay the hospital for my visit",
        "what do I owe the doctor's office",
    ],
    "premium_due": [
        "when is my premium due",
        "how much is my monthly premium",
        "is autopay turned on",
        "when do I need to pay my insurance bill",
    ],
    "policy_summary": [
        "what plan am I on",
        "is my policy active",
        "give me a summary of my policy",
        "tell me about my plan",
        "am I covered right now",
        "is my insurance still active",
        "when did my policy start",
        "can I still cancel my policy for a refund",
    ],
    "riders": [
        "do I have any riders",
        "which add-ons are on my policy",
        "do I have dental cover",
        "is vision added to my plan",
        "what extra coverage did I buy",
    ],
    "waiting_period": [
        "do I have any waiting periods",
        "when does my waiting period end",
        "when can I get my knee surgery covered",
        "am I still in a waiting period",
        "what treatments are not covered yet because I'm new",
    ],
    "raise_claim": [
        "how do I raise a claim",
        "how to file a claim",
        "what are the steps to submit a claim",
        "how do I get reimbursed for a bill I paid",
        "what documents do I need to make a claim",
        "how do I make a cashless claim at the hospital",
        "where is the claim form",
        "I paid out of pocket, how do I get the money back",
    ],
    "general_question": [
        "what is prior approval",
        "do I need a referral to see a specialist",
        "can I see a dermatologist without asking my doctor first",
        "what counts toward the deductible",
        "what is coinsurance",
        "how long does a claim take to process",
        "how do I appeal a denied claim",
        "what happens if I skip prior approval",
        "will I get a bill if my scan was not approved",
        "is emergency care covered at an out-of-network hospital",
        "can I use telehealth video visits",
        "how do I find an in-network doctor",
        # Insurance jargon (answered from data/docs/insurance-terms.md)
        "what does ex gratia mean",
        "what is a cashless claim",
        "what is the difference between cashless and reimbursement",
        "what happens if my policy lapses",
        "what is a waiting period",
        "what is a rider",
        "what does add-on coverage mean",
        "what does pre-existing condition mean",
        "explain this insurance term",
    ],
    "handoff": [
        "I want to talk to a person",
        "connect me to an agent",
        "can I speak to a human",
        "please call me",
        "this is not helping, get me a representative",
    ],
    "greeting": ["hi", "hello there", "thanks", "thank you", "what can you do", "help"],
}

# nomic-embed-text task prefix for classification-style comparisons.
_PREFIX = "classification: "
# Below this similarity we treat the question as "unknown" (then plan docs are searched).
MIN_SCORE = 0.72

_example_vectors: list[tuple[str, list[float]]] | None = None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


async def _examples() -> list[tuple[str, list[float]]]:
    global _example_vectors
    if _example_vectors is None:
        pairs = [(intent, text) for intent, texts in EXAMPLES.items() for text in texts]
        vectors = await embed([_PREFIX + text for _, text in pairs])
        _example_vectors = [(intent, vec) for (intent, _), vec in zip(pairs, vectors, strict=True)]
    return _example_vectors


async def route(redacted_text: str) -> tuple[str, float, dict[str, float]]:
    """Returns (best intent or "unknown", best score, best score per intent). Raises LLMUnavailable."""
    examples = await _examples()
    [query] = await embed([_PREFIX + redacted_text])
    per_intent: dict[str, float] = {}
    for intent, vec in examples:
        per_intent[intent] = max(per_intent.get(intent, -1.0), _cosine(query, vec))
    best = max(per_intent, key=per_intent.__getitem__)
    score = per_intent[best]
    return (best if score >= MIN_SCORE else "unknown"), score, per_intent
