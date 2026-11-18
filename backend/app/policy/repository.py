"""Policy data access. Prototype: reads fake JSON files. Later: swap for a real database."""

import json
from datetime import date
from functools import lru_cache
from typing import Any

from app.core.config import settings

Policy = dict[str, Any]
Plan = dict[str, Any]


@lru_cache
def _load(filename: str) -> dict[str, Any]:
    return json.loads((settings.data_dir / filename).read_text(encoding="utf-8"))


def normalize_policy_number(value: str) -> str:
    """'hl100234' / 'HL-100234' / ' hl-100234 ' → 'HL-100234'."""
    compact = value.strip().upper().replace("-", "").replace(" ", "")
    return f"{compact[:2]}-{compact[2:]}" if compact[:2].isalpha() else compact


def _find(policy_number: str) -> Policy | None:
    wanted = normalize_policy_number(policy_number)
    return next((p for p in _load("policies.json")["policies"] if p["policy_number"] == wanted), None)


def verify(policy_number: str, dob: date) -> str | None:
    """Returns the policy ID when number + date of birth match, else None."""
    policy = _find(policy_number)
    if policy and date.fromisoformat(policy["dob"]) == dob:
        return policy["policy_number"]
    return None


def get_policy(policy_id: str) -> Policy:
    policy = _find(policy_id)
    if policy is None:
        raise LookupError("Unknown policy")
    return policy


def get_plan(plan_id: str) -> Plan:
    return _load("plans.json")["plans"][plan_id]


def find_coverage(plan: Plan, *queries: str | None) -> dict[str, Any] | None:
    """Matches a service the customer asked about (e.g. 'knee MRI') to a coverage entry."""
    for query in queries:
        if not query:
            continue
        q = query.lower()
        # Longest alias first, so "physical therapy" beats "therapy" and "physical".
        matches = [
            (len(alias), entry) for entry in plan["coverage"].values() for alias in entry["aliases"] if alias in q
        ]
        if matches:
            return max(matches, key=lambda m: m[0])[1]
    return None
