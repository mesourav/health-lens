"""Client for OUR OWN model server (Ollama). No third-party AI APIs are called anywhere.

Callers must only send redacted text or general plan documents — never policy data.
If the model server is unreachable, LLMUnavailable is raised and callers fall back
to keyword logic, so the prototype still works without a model.
"""

import json
import logging
import time
from typing import Any

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_METADATA_TOKEN_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
_token: tuple[str, float] | None = None


class LLMUnavailable(Exception):
    pass


async def _auth_headers(client: httpx.AsyncClient) -> dict[str, str]:
    """On Cloud Run the model service is private: call it with a Google-signed ID token."""
    global _token
    if not settings.ollama_use_id_token:
        return {}
    if _token is None or _token[1] < time.time():
        res = await client.get(
            _METADATA_TOKEN_URL,
            params={"audience": settings.ollama_url},
            headers={"Metadata-Flavor": "Google"},
        )
        res.raise_for_status()
        _token = (res.text, time.time() + 45 * 60)  # tokens live 1h; refresh early
    return {"Authorization": f"Bearer {_token[0]}"}


# After a connection failure, skip the model for a while instead of waiting on it every call.
_RETRY_AFTER_S = 30.0
_down_until = 0.0


async def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    global _down_until
    if time.monotonic() < _down_until:
        raise LLMUnavailable("model server marked down; retrying later")
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
            headers = await _auth_headers(client)
            res = await client.post(f"{settings.ollama_url}{path}", json=payload, headers=headers)
            res.raise_for_status()
            return res.json()
    except httpx.ConnectError as exc:
        _down_until = time.monotonic() + _RETRY_AFTER_S
        log.warning("Model server unreachable (%s); using fallback for %ss", exc, _RETRY_AFTER_S)
        raise LLMUnavailable(str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("LLM call to %s failed: %s", path, exc)
        raise LLMUnavailable(str(exc)) from exc


async def chat(system: str, user: str, *, schema: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "model": settings.chat_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": 0},
    }
    if schema:
        payload["format"] = schema  # Ollama structured output: reply is JSON matching schema
    return (await _post("/api/chat", payload))["message"]["content"].strip()


async def chat_json(system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
    raw = await chat(system, user, schema=schema)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMUnavailable(f"Model returned invalid JSON: {raw[:200]}") from exc


async def embed(texts: list[str]) -> list[list[float]]:
    data = await _post("/api/embed", {"model": settings.embed_model, "input": texts})
    return data["embeddings"]
