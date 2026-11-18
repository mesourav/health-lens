"""RAG over GENERAL plan documents (data/docs/*.md). Never index customer data here.

1. Load: each markdown file is split into one chunk per "## " section.
2. Embed: chunks are turned into vectors by our own embedding model (Ollama), cached on disk.
3. Search: the question is embedded and compared to every chunk (cosine similarity).
   Prototype keeps vectors in memory — fine for dozens of documents. Later: pgvector.
If the model server is down, search falls back to simple keyword overlap.
"""

import hashlib
import json
import logging
import math
import re
from dataclasses import asdict, dataclass

from app.core.config import settings
from app.llm.ollama import LLMUnavailable, embed

log = logging.getLogger(__name__)

# nomic-embed-text works best with these task prefixes; harmless for other models.
_DOC_PREFIX = "search_document: "
_QUERY_PREFIX = "search_query: "

_WORD = re.compile(r"[a-z]+")
_STOPWORDS = set(
    "a an the is are am do does did i my me we you your it of to in on for and or what how "
    "can should would will be with at by about this that if need get have has".split()
)


@dataclass
class Chunk:
    doc_title: str
    section: str
    text: str

    @property
    def source(self) -> str:
        return f"{self.doc_title} › {self.section}"


_chunks: list[Chunk] | None = None
_vectors: list[list[float]] | None = None


def load_chunks() -> list[Chunk]:
    global _chunks
    if _chunks is None:
        _chunks = []
        for path in sorted((settings.data_dir / "docs").glob("*.md")):
            content = path.read_text(encoding="utf-8")
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else path.stem
            for block in re.split(r"^## ", content, flags=re.MULTILINE)[1:]:
                heading, _, body = block.partition("\n")
                _chunks.append(Chunk(title, heading.strip(), " ".join(body.split())))
    return _chunks


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


async def _get_vectors(chunks: list[Chunk]) -> list[list[float]]:
    global _vectors
    if _vectors is not None:
        return _vectors

    fingerprint = hashlib.sha256(json.dumps([settings.embed_model, [asdict(c) for c in chunks]]).encode()).hexdigest()
    cache_file = settings.data_dir / ".cache" / f"rag-{fingerprint[:16]}.json"
    if cache_file.exists():
        _vectors = json.loads(cache_file.read_text())
        return _vectors

    log.info("Embedding %d plan-document chunks…", len(chunks))
    _vectors = await embed([f"{_DOC_PREFIX}{c.section}. {c.text}" for c in chunks])
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(_vectors))
    return _vectors


def _keyword_search(question: str, chunks: list[Chunk], k: int) -> list[tuple[float, Chunk]]:
    terms = {w for w in _WORD.findall(question.lower()) if w not in _STOPWORDS}
    if not terms:
        return []

    def hits(text: str) -> int:
        words = set(_WORD.findall(text.lower()))
        # Prefix match so "approve" finds "approval".
        return sum(1 for t in terms if any(w.startswith(t[:5]) for w in words))

    scored = []
    for chunk in chunks:
        # Heading matches count double: "What is prior approval?" beats a passing mention.
        body_hits = hits(f"{chunk.section} {chunk.text}")
        score = (body_hits + hits(chunk.section)) / (2 * len(terms))
        scored.append((score, chunk))
    return sorted(scored, key=lambda s: s[0], reverse=True)[:k]


# Below these scores, we say "I don't know" instead of guessing.
EMBED_MIN_SCORE = 0.62  # measured: relevant ≈ 0.66–0.83, unrelated ≈ 0.45–0.59
KEYWORD_MIN_SCORE = 0.5


async def search(question: str, k: int = 3) -> tuple[list[tuple[float, Chunk]], float]:
    """Returns (top-k (score, chunk) pairs, minimum score to trust)."""
    chunks = load_chunks()
    try:
        vectors = await _get_vectors(chunks)
        [query_vec] = await embed([f"{_QUERY_PREFIX}{question}"])
    except LLMUnavailable:
        return _keyword_search(question, chunks, k), KEYWORD_MIN_SCORE
    scored = sorted(
        ((_cosine(query_vec, v), c) for v, c in zip(vectors, chunks, strict=True)),
        key=lambda s: s[0],
        reverse=True,
    )
    return scored[:k], EMBED_MIN_SCORE
