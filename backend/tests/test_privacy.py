from app.privacy.redact import redact


def test_redacts_personal_details() -> None:
    text = "I'm Jordan, policy HL-100234, born 1988-04-12, call +1 (555) 123-4567 or j@x.com"
    out = redact(text, names=["Jordan"])
    for secret in ("Jordan", "HL-100234", "1988-04-12", "555", "j@x.com"):
        assert secret not in out
    assert "[POLICY_NO]" in out and "[NAME]" in out


def test_keeps_the_question() -> None:
    assert redact("Is an MRI covered?") == "Is an MRI covered?"
