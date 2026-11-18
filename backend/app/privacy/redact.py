"""Strips personal details from customer text before it is sent to the AI model.

Prototype: regex rules. Later: Microsoft Presidio (still runs locally) for names/addresses.
"""

import re

_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
    (re.compile(r"\b[A-Z]{2,3}-?\d{5,}\b", re.IGNORECASE), "[POLICY_NO]"),
    (re.compile(r"\b\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}\b"), "[DATE]"),
    (re.compile(r"\+?\d[\d\s().-]{7,}\d"), "[PHONE]"),
    (re.compile(r"\b\d{6,}\b"), "[NUMBER]"),
]


def redact(text: str, names: list[str] | None = None) -> str:
    for pattern, placeholder in _RULES:
        text = pattern.sub(placeholder, text)
    for name in names or []:
        if name:
            text = re.sub(rf"\b{re.escape(name)}\b", "[NAME]", text, flags=re.IGNORECASE)
    return text
