"""Answers PERSONAL questions from policy data with plain templates. No AI involved here.

This is the core privacy idea: real values are filled in by code, after (and without) the model.
"""

from datetime import date, timedelta

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
    if oop_left <= 0:
        second = (
            f"You've also reached your {_money(oop['total'])} out-of-pocket maximum, "
            "so covered in-network care is now 100% paid for the rest of the year."
        )
    else:
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
        text = f"No, your {plan['name']} plan doesn't cover {entry['label'].lower()}. {entry['cost']}."
    replies = [R.PRIOR] if entry["prior_approval"] else []
    return _bot(text, [*replies, R.DEDUCTIBLE, R.PERSON])


def claim_status(policy: Policy) -> ChatTurn:
    claims = sorted(policy["claims"], key=lambda c: c["date"], reverse=True)[:3]
    if not claims:
        return _bot("You don't have any claims this year.")
    lines = []
    for c in claims:
        owe = f"you owe {_money(c['you_owe'])}" if c["you_owe"] is not None else "amount not final yet"
        status = c["status"].capitalize()
        if c.get("ex_gratia"):
            status += f", but we made an ex gratia (goodwill) payment of {_money(c['ex_gratia'])}"
        lines.append(f"• {_date(c['date'])}: {c['service']} at {c['provider']}. {status}, {owe}.")
    return _bot("Here are your most recent claims:\n" + "\n".join(lines), [R.CLAIMS_HOWTO, R.MORE, R.PERSON])


def premium_due(policy: Policy) -> ChatTurn:
    p = policy["premium"]
    plan = get_plan(policy["plan_id"])
    text = f"Your monthly premium is {_money(p['monthly'])}, next due on {_date(p['next_due'])}."
    text += (
        " Autopay is on, so it will be paid automatically."
        if p["autopay"]
        else " Autopay is off. You can pay in the member portal or turn on autopay there."
    )
    text += f" If a payment is ever late, you have a {plan['grace_period_days']}-day grace period to pay it."
    return _bot(text)


def policy_summary(policy: Policy) -> ChatTurn:
    plan = get_plan(policy["plan_id"])
    ded = policy["deductible"]
    text = (
        f"You're on the {plan['name']} plan, and your policy is {policy['status']}. "
        f"It started on {_date(policy['start_date'])}. "
        f"Your deductible is {_money(ded['total'])} a year and your out-of-pocket maximum is "
        f"{_money(policy['out_of_pocket_max']['total'])}."
    )
    free_look_ends = date.fromisoformat(policy["start_date"]) + timedelta(days=plan["free_look_days"])
    if date.today() < free_look_ends:
        text += (
            f" You're still in your {plan['free_look_days']}-day free look period until "
            f"{_date(free_look_ends.isoformat())}, so you can cancel for a full refund of your premium."
        )
    return _bot(text, [R.DEDUCTIBLE, R.CLAIMS, R.PERSON])


def riders(policy: Policy) -> ChatTurn:
    items = policy["riders"]
    if not items:
        return _bot("You don't have any riders (add-ons) on your policy. Only your main plan's coverage applies.")
    names = [f"{r['name']} ({_money(r['monthly'])} a month)" for r in items]
    listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    noun = "rider" if len(items) == 1 else "riders"
    return _bot(f"You have {len(items)} {noun} (add-ons) on your policy: {listed}.")


def waiting_periods(policy: Policy) -> ChatTurn:
    today = date.today()
    active = [w for w in policy["waiting_periods"] if date.fromisoformat(w["ends"]) > today]
    if not active:
        return _bot("You don't have any waiting periods, so all of your plan's covered care is available now.")
    lines = [f"• {w['treatment']}: covered from {_date(w['ends'])}" for w in active]
    return _bot(
        "These treatments are still in a waiting period on your policy:\n"
        + "\n".join(lines)
        + "\nEmergency care is always covered."
    )
