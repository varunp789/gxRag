"""Deterministic text utilities shared by the pipeline and the retrieval engine."""

from __future__ import annotations

import re
from itertools import combinations

_STOPWORDS = frozenset(
    "a an and are as at be by for from has have in is it its of on or that the this to was were will with".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")
_ENTITY = re.compile(r"\b[A-Z][A-Za-z0-9&\-]{2,}(?:\s+[A-Z][A-Za-z0-9&\-]{2,})*")


def tokenize(text: str) -> list[str]:
    return [token for token in _TOKEN.findall(text.lower()) if token not in _STOPWORDS]


def chunk_text(text: str, size: int = 1000, overlap: int = 100) -> list[str]:
    """Split on paragraph/sentence boundaries into ~``size`` character chunks."""
    text = text.strip()
    if not text:
        return []
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n{2,}", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > size:  # hard-wrap pathological unbroken text
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:size])
            sentence = sentence[size - overlap:]
        if current and len(current) + len(sentence) + 1 > size:
            chunks.append(current)
            current = current[-overlap:] + " " + sentence if overlap else sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def extract_entities(text: str, limit: int = 100) -> list[str]:
    """Capitalised phrases, minus sentence-initial common words."""
    found: dict[str, int] = {}
    for match in _ENTITY.finditer(text):
        phrase = match.group(0).strip()
        if phrase.lower() in _STOPWORDS or len(phrase) < 3:
            continue
        found[phrase] = found.get(phrase, 0) + 1
    ranked = sorted(found, key=lambda name: (-found[name], name))
    return ranked[:limit]


def extract_relations(chunks: list[str], entities: list[str], limit: int = 500) -> list[tuple[str, str]]:
    """Entities co-occurring in a chunk are related (undirected, deduplicated)."""
    known = set(entities)
    relations: dict[tuple[str, str], int] = {}
    for chunk in chunks:
        present = sorted({entity for entity in known if entity in chunk})
        for left, right in combinations(present, 2):
            relations[(left, right)] = relations.get((left, right), 0) + 1
    ranked = sorted(relations, key=lambda pair: (-relations[pair], pair))
    return ranked[:limit]
