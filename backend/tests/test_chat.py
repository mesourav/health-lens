from fastapi.testclient import TestClient

CID = "conv-1"


def send(client: TestClient, **body) -> dict:
    res = client.post("/api/chat", json={"conversationId": CID, "mode": "bot", **body})
    assert res.status_code == 200, res.text
    return res.json()


def text_of(turn: dict) -> str:
    return " ".join(step["text"] for step in turn["steps"])


def login(client: TestClient, policy: str = "HL-100234", dob: str = "1988-04-12") -> dict:
    send(client, intent="start")
    send(client, text=f"my policy is {policy}")
    return send(client, text=dob)


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_requires_intent_or_text(client: TestClient) -> None:
    res = client.post("/api/chat", json={"conversationId": CID, "mode": "bot"})
    assert res.status_code == 422


def test_start_asks_for_policy_number(client: TestClient) -> None:
    turn = send(client, intent="start")
    assert "policy number" in text_of(turn)
    assert "followUp" not in turn  # None fields are dropped, camelCase on the wire


def test_login_then_personal_answer(client: TestClient) -> None:
    assert "Jordan" in text_of(login(client))
    assert "$640 to go" in text_of(send(client, intent="deductible"))


def test_typed_personal_question_uses_policy_data(client: TestClient) -> None:
    login(client)
    turn = send(client, text="is a knee MRI covered?")
    assert "20% coinsurance" in text_of(turn)


def test_each_customer_sees_their_own_plan(client: TestClient) -> None:
    login(client, "hl200871", "30/11/1975")
    assert "10% coinsurance" in text_of(send(client, intent="mri"))  # Gold plan, not Silver


def test_wrong_dob_is_rejected_without_saying_which_field(client: TestClient) -> None:
    turn = login(client, dob="2000-01-01")
    assert "don't match" in text_of(turn)
    assert "Jordan" not in text_of(turn)


def test_lockout_after_three_failures(client: TestClient) -> None:
    send(client, intent="start")
    for _ in range(3):
        send(client, text="HL-100234")
        turn = send(client, text="2000-01-01")
    assert "paused" in text_of(turn)


def test_personal_question_before_login_asks_to_verify(client: TestClient) -> None:
    send(client, intent="start")
    turn = send(client, intent="deductible")
    assert "verified" in text_of(turn)
    assert "$" not in text_of(turn)


def test_general_question_uses_plan_docs_without_login(client: TestClient) -> None:
    send(client, intent="start")
    turn = send(client, intent="prior")
    assert "Source: Prior Approval Guide" in text_of(turn)


def test_restart_logs_out(client: TestClient) -> None:
    login(client)
    client.post("/api/chat", json={"conversationId": "conv-2", "mode": "bot", "intent": "start"})
    res = client.post("/api/chat", json={"conversationId": "conv-2", "mode": "bot", "intent": "deductible"})
    assert "verified" in text_of(res.json())


def test_handoff_queues_and_agent_joins(client: TestClient) -> None:
    send(client, intent="start")
    queued = send(client, intent="queue")
    assert queued["followUp"] == {"intent": "agentJoin", "delayMs": 4000}
    assert send(client, intent="agentJoin")["mode"] == "agent"


def test_personal_jargon_answers(client: TestClient) -> None:
    login(client, "HL-200871", "1975-11-30")  # Priya: two riders, an ex gratia claim
    assert "Dental ($22 a month) and Vision ($9 a month)" in text_of(send(client, text="do I have any riders?"))
    assert "ex gratia (goodwill) payment of $400" in text_of(send(client, intent="claims"))
    assert "30-day grace period" in text_of(send(client, intent="premium"))


def test_waiting_periods_for_new_member(client: TestClient) -> None:
    login(client, "HL-300415", "1996-07-08")  # Marcus: new member
    text = text_of(send(client, text="when does my waiting period end?"))
    assert "Planned knee or hip replacement" in text
    assert "Emergency care is always covered" in text


def test_jargon_definition_needs_no_login(client: TestClient) -> None:
    text = text_of(send(client, text="What is a rider?"))
    assert "Insurance Terms Explained" in text
    assert "policy number" not in text


def test_raise_claim_steps_before_login(client: TestClient) -> None:
    text = text_of(send(client, text="How do I raise a claim?"))
    assert "Cashless claim" in text and "Reimbursement claim" in text
    assert "Submit within 90 days of the date of care." in text
    assert "policy number HL-" not in text  # nothing personal before login


def test_raise_claim_reimbursement_only_when_logged_in(client: TestClient) -> None:
    login(client)
    text = text_of(send(client, text="how do I get reimbursed for a bill I paid?"))
    assert "Reimbursement claim" in text and "Cashless claim" not in text
    assert "Itemized bill" in text
    assert "Quote your policy number HL-100234" in text
