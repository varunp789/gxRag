from app.services.search import Chunk, bm25, hybrid_search, trigram_vector, vector_search
from app.services.text import chunk_text, extract_entities, extract_relations, tokenize


def test_chunking_respects_size_and_covers_text():
    text = " ".join(f"Sentence number {i} talks about Orbit." for i in range(200))
    chunks = chunk_text(text, size=300, overlap=30)
    assert len(chunks) > 5 and all(len(c) <= 340 for c in chunks)
    assert "Sentence number 199" in chunks[-1]


def test_chunking_handles_empty_and_unbroken_text():
    assert chunk_text("   ") == []
    long = "x" * 2500
    assert all(len(c) <= 1000 for c in chunk_text(long))


def test_entities_and_relations():
    text = "Orbit Bio Labs works with Harborview Hospital. Harborview Hospital is in Boston. Nothing else here."
    entities = extract_entities(text)
    assert {"Orbit Bio Labs", "Harborview Hospital", "Boston"} <= set(entities)
    relations = extract_relations([text], entities)
    assert ("Harborview Hospital", "Orbit Bio Labs") in relations


def test_tokenize_drops_stopwords():
    assert tokenize("The Quick brown fox is on the mat") == ["quick", "brown", "fox", "mat"]


def _chunks(*texts):
    return [Chunk(asset_id=f"a{i}", artifact_id="x", index=0, text=t, tokens=tokenize(t)) for i, t in enumerate(texts)]


def test_bm25_ranks_rarer_terms_higher():
    chunks = _chunks("alpha beta common", "alpha common common", "gamma common")
    ranked = bm25(chunks, "alpha beta")
    assert ranked[0].chunk.asset_id == "a0" and len(ranked) == 2
    assert bm25(chunks, "zzz") == [] and bm25([], "alpha") == []


def test_vector_matches_morphological_variants_and_rejects_unrelated():
    chunks = _chunks("The trials of the inhibitor were completed", "Bond coupon schedules for municipal debt")
    assert vector_search(chunks, "inhibitors trial")[0].chunk.asset_id == "a0"
    assert vector_search(chunks, "lattice chromodynamics") == []


def test_vector_is_normalised_and_deterministic():
    vector = trigram_vector("hello world")
    assert abs(sum(v * v for v in vector) - 1.0) < 1e-9 and vector == trigram_vector("hello world")


def test_hybrid_fuses_both_signals():
    chunks = _chunks("kelvar pathway inhibitor", "bond ledger", "kelvar")
    assert hybrid_search(chunks, "kelvar pathway")[0].chunk.asset_id == "a0"
