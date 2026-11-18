import pytest
from fastapi.testclient import TestClient

from app.llm import ollama
from app.main import app


@pytest.fixture(autouse=True)
def no_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests run without a model server: every LLM call takes the fallback path."""

    async def unavailable(*_args, **_kwargs):
        raise ollama.LLMUnavailable("disabled in tests")

    monkeypatch.setattr(ollama, "_post", unavailable)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)  # keeps cookies between requests, like a browser
