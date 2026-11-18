"""Answers a general question from plan documents (Retrieval-Augmented Generation).

Retrieval decides IF we can answer (similarity score). The chat model only rewrites the
retrieved text into a friendly reply. If its reply looks unusable, we show the passage itself,
so the answer is always grounded in our documents.
"""

import re
from dataclasses import dataclass

from app.llm.ollama import LLMUnavailable, chat
from app.rag.index import search

_SYSTEM = """You are a friendly health insurance help assistant.
Answer the member's question using the plan document excerpts provided.
Write 2 to 4 short sentences in plain language. Include the specific details from the excerpts
that answer the question (timeframes, what is covered, what to do next).
No markdown, no lists, no greetings. Do not add facts that are not in the excerpts."""

_MIN_ANSWER_CHARS = 80  # shorter than this = the small model dropped the details


@dataclass
class RagAnswer:
    text: str
    sources: list[str]


async def answer_general(question: str) -> RagAnswer | None:
    """`question` must already be redacted. Returns None when the docs don't cover it."""
    results, min_score = await search(question)
    if not results or results[0][0] < min_score:
        return None
    # Keep only sections nearly as relevant as the best one, so the AI isn't fed loosely related text.
    best_score = results[0][0]
    relevant = [chunk for score, chunk in results if score >= min_score and score >= best_score - 0.06]
    best = relevant[0]
    passage_answer = RagAnswer(best.text, [best.source])

    context = "\n\n".join(f"[{c.section}]\n{c.text}" for c in relevant)
    try:
        text = await chat(_SYSTEM, f"Plan document excerpts:\n{context}\n\nQuestion: {question}")
    except LLMUnavailable:
        return passage_answer

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < _MIN_ANSWER_CHARS or "NOT_FOUND" in text or "excerpt" in text.lower():
        return passage_answer
    return RagAnswer(text, [c.source for c in relevant[:2]])
