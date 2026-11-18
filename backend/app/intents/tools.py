"""Answers PERSONAL questions from policy data with plain templates. No AI involved here.

This is the core privacy idea: real values are filled in by code, after (and without) the model.
"""

from datetime import date

from app.intents import replies as R
from app.policy.repository import Policy, find_coverage, get_plan
from app.schemas.chat import BotStep, ChatTurn


def _money(value: float) -> str:
    return f"${value:,.2f}" if value % 1 else f"${value:,.0f}"


def _date(value: str) -> str:
    d = date.fromisoformat(value)
    return f"{d:%B} {d.day}, {d.year}"


def _bot(text: str, replies: list | None = None) -> ChatTurn:
    return ChatTurn(steps=[BotStep(sender="bot", text=text)], replies=replies or [R.MORE, R.PERSON])


def deductible_status(policy: Policy) -> ChatTurn:
    ded, oop = policy["deductible"], policy["out_of_pocket_max"]
    left = ded["total"] - ded["used"]
    if left <= 0:
        first = f"You've met your {_money(ded['total'])} deductible for this year."
    else:
        first = (
            f"You've paid {_money(ded['used'])} of your {_money(ded['total'])} deductible "
            f"this year, so you have {_money(left)} to go."
        )
    oop_left = oop["total"] - oop["used"]
    second = (
        f"You've also paid {_money(oop['used'])} toward your {_money(oop['total'])} "
        f"out-of-pocket maximum ({_money(oop_left)} left). After that, covered in-network care is 100% paid."
    )
    return _bot(f"{first} {second}", [R.COUNTS, R.MORE, R.PERSON])


def coverage_check(policy: Policy, service: str | None, original_text: str | None) -> ChatTurn | None:
    """Returns None if we can't match the service — caller then tries the plan documents."""
    plan = get_plan(policy["plan_id"])
    entry = find_coverage(plan, service, original_text)
    if entry is None:
        return None
    if entry["covered"]:
        label = entry["label"]
        if not label.split()[0].isupper():  # keep acronyms like "MRI", lowercase "Therapy"
            label = label[0].lower() + label[1:]
        text = f"Yes, your {plan['name']} plan covers {label}: {entry['cost']}."
        if entry["prior_approval"]:
            text += " You'll need prior approval first; your doctor's office usually handles that."
    else:
        text = f"{entry['label']} isn't covered on your {plan['name']} plan. {entry['cost']}."
    replies = [R.PRIOR] if entry["prior_approval"] else []
    return _bot(text, [*replies, R.DEDUCTIBLE, R.PERSON])


def claim_status(policy: Policy) -> ChatTurn:
    claims = sorted(policy["claims"], key=lambda c: c["date"], reverse=True)[:3]
    if not claims:
        return _bot("You don't have any claims this year.")
    lines = []
    for c in claims:
        owe = f"you owe {_money(c['you_owe'])}" if c["you_owe"] is not None else "amount not final yet"
        lines.append(f"• {_date(c['date'])}: {c['service']} at {c['provider']}. {c['status'].capitalize()}, {owe}.")
    return _bot("Here are your most recent claims:\n" + "\n".join(lines), [R.CLAIMS_HOWTO, R.MORE, R.PERSON])


def premium_due(policy: Policy) -> ChatTurn:
    p = policy["premium"]
    text = f"Your monthly premium is {_money(p['monthly'])}, next due on {_date(p['next_due'])}."
    text += (
        " Autopay is on, so it will be paid automatically."
        if p["autopay"]
        else " Autopay is off. You can pay in the member portal or turn on autopay there."
    )
    return _bot(text)


def policy_summary(policy: Policy) -> ChatTurn:
    plan = get_plan(policy["plan_id"])
    ded = policy["deductible"]
    text = (
        f"You're on the {plan['name']} plan, and your policy is {policy['status']}. "
        f"Your deductible is {_money(ded['total'])} a year and your out-of-pocket maximum is "
        f"{_money(policy['out_of_pocket_max']['total'])}."
    )
    return _bot(text, [R.DEDUCTIBLE, R.CLAIMS, R.PERSON])
