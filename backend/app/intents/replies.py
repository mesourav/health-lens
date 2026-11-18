"""Quick-reply chips. Each `intent` comes back to the backend when tapped."""

from app.schemas.chat import QuickReply

MRI = QuickReply(label="Is an MRI covered?", intent="mri")
DEDUCTIBLE = QuickReply(label="How much deductible is left?", intent="deductible")
CLAIMS = QuickReply(label="My recent claims", intent="claims")
PREMIUM = QuickReply(label="When is my premium due?", intent="premium")
THERAPY = QuickReply(label="Is therapy covered?", intent="therapy")
PRIOR = QuickReply(label="What is prior approval?", intent="prior")
REFERRAL = QuickReply(label="Do I need a referral?", intent="referral")
COUNTS = QuickReply(label="What counts toward it?", intent="counts")
CLAIMS_HOWTO = QuickReply(label="How long do claims take?", intent="claims_howto")
RAISE_CLAIM = QuickReply(label="How do I raise a claim?", intent="raise_claim")
PERSON = QuickReply(label="Talk to a person", intent="handoff")
MORE = QuickReply(label="Ask something else", intent="menu")

MAIN = [MRI, DEDUCTIBLE, CLAIMS, PREMIUM, PERSON]
BEFORE_LOGIN = [PRIOR, REFERRAL, RAISE_CLAIM]

# Quick-reply intents that are general questions → answered from plan docs (RAG).
GENERAL_QUESTIONS = {
    "prior": "What is prior approval?",
    "referral": "Do I need a referral to see a specialist?",
    "counts": "What counts toward the deductible?",
    "claims_howto": "How long does a claim take?",
}
