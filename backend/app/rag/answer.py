"""Answers a general question from plan documents (Retrieval-Augmented Generation)."""

from dataclasses import dataclass

from app.llm.ollama import LLMUnavailable, chat
from app.rag.index import search

_SYSTEM = """You are a health insurance help assistant.
Answer the member's question using ONLY the plan document excerpts provided.
If the excerpts do not contain the answer, reply exactly: NOT_FOUND
Rules: 2-4 short, friendly sentences. Plain language. No markdown, no lists.
Do not invent numbers, prices or rules that are not in the excerpts."""


@dataclass
class RagAnswer:
    text: str
    sources: list[str]


async def answer_general(question: str) -> RagAnswer | None:
    """`question` must already be redacted. Returns None when the docs don't cover it."""
    results, min_score = await search(question)
    relevant = [chunk for score, chunk in results if score >= min_score]
    if not relevant:
        return None

    context = "\n\n".join(f"[{c.source}]\n{c.text}" for c in relevant)
    try:
        text = await chat(_SYSTEM, f"Plan document excerpts:\n{context}\n\nQuestion: {question}")
    except LLMUnavailable:
        # No model available: show the best-matching passage as-is.
        best = relevant[0]
        return RagAnswer(best.text, [best.source])

    if "NOT_FOUND" in text:
        return None
    return RagAnswer(text, list(dict.fromkeys(c.source for c in relevant[:2])))
