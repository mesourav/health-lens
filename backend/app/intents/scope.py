"""Scope guard: we only handle Health, Term and Life insurance.

Plain code (no AI), checked before a message is classified. A message is out of scope when it
names another kind of insurance (vehicle, home, travel...) AND says nothing about health or life
cover. So "claim vehicle" is declined, but "car accident, is my hospital stay covered?" is not.
"""

import re

SUPPORTED_LINES = ("Health", "Term", "Life")

# Other kinds of insurance → the words that give them away. Ambiguous words are only matched
# as phrases: "PET scan" and "home care" are health questions, "pet insurance" is not.
_OTHER_LINES: dict[str, list[str]] = {
    "vehicle": [
        "vehicle",
        "car",
        "cars",
        "motor",
        "bike",
        "motorbike",
        "motorcycle",
        "scooter",
        "two-wheeler",
        "two wheeler",
        "truck",
        "automobile",
        "auto insurance",
        "number plate",
        "windshield",
        "windscreen",
    ],
    "home or property": [
        "home insurance",
        "house",
        "flood",
        "flooded",
        "stolen",
        "property",
        "burglary",
        "theft",
        "flood damage",
        "fire damage",
        "contents insurance",
        "renters insurance",
        "home loan",
    ],
    "travel": ["travel insurance", "flight", "baggage", "luggage", "trip cancellation", "passport"],
    "pet": ["pet insurance", "my dog", "my cat", "vet bill", "veterinary"],
    "gadget": ["phone insurance", "mobile insurance", "gadget", "laptop insurance", "screen damage"],
    "business or marine": [
        "marine",
        "cargo",
        "shipment",
        "crop insurance",
        "business insurance",
        "liability insurance",
    ],
}

# If any of these appear, the customer is asking about health or life cover, so we answer.
_IN_SCOPE = re.compile(
    r"\b(health|medical|hospital|doctor|injur|treatment|surgery|medicine|prescription|therapy|"
    r"term (insurance|plan|policy|cover)|life|death|nominee|mri|scan|illness|sick)",
    re.I,
)


def _pattern(words: list[str]) -> re.Pattern[str]:
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.I)


_OTHER_PATTERNS = {line: _pattern(words) for line, words in _OTHER_LINES.items()}


def out_of_scope_line(text: str) -> str | None:
    """Returns the kind of insurance asked about (e.g. "vehicle") if we don't cover it, else None."""
    if _IN_SCOPE.search(text):
        return None
    for line, pattern in _OTHER_PATTERNS.items():
        if pattern.search(text):
            return line
    return None
