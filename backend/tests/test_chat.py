from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_start_returns_camelcase_turn() -> None:
    res = client.post("/api/chat", json={"conversationId": "c1", "mode": "bot", "intent": "start"})
    assert res.status_code == 200
    body = res.json()
    assert body["steps"][0]["sender"] == "bot"
    assert body["replies"]
    assert "follow_up" not in body


def test_requires_intent_or_text() -> None:
    res = client.post("/api/chat", json={"conversationId": "c1", "mode": "bot"})
    assert res.status_code == 422
