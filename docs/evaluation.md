# Evaluation dataset and release gates

The gold set lives in `apps/api/eval/corpus.py` and is run by `python -m eval.run` (also as a pytest in
`tests/test_eval_gate.py` and as a CI step that uploads `eval-report.json`). It drives the real API and
worker: upload -> queued job -> extraction -> chunking/entities/relations -> retrieval.

| Modality | In gold set | Extraction path |
|---|---|---|
| Web HTML | 3 pages | `html.parser` |
| Spreadsheet / CSV | 2 tables | `csv` / `pandas` |
| PDF | 2 documents (generated, text layer) | `pypdf` |
| Image (OCR) | **not evaluated** - needs `tesseract` + labelled images | |
| Audio (STT) | **not evaluated** - needs a provider key + labelled audio | |

Metrics and thresholds (`apps/api/eval/thresholds.json`; a miss fails CI and the release):

| Metric | Threshold | Meaning |
|---|---|---|
| `retrieval_recall_at_5` | 0.90 | expected asset appears in top 5 across vector / hybrid / multimodal / structured queries |
| `retrieval_mrr` | 0.70 | mean reciprocal rank of the first expected asset |
| `graph_entity_recall` / `graph_relation_recall` | 0.75 / 0.50 | labelled entities and co-occurrence relations found per asset |
| `graph_expansion_recall` | 1.00 | graph mode reaches a second asset through a shared entity |
| `citation_coverage` | 1.00 | every result has a citation with a known asset, artifact id and provenance |
| `negative_query_precision` | 1.00 | queries with no evidence return nothing |
| `extraction_success_rate` | 1.00 | every gold asset reaches `ready` |

**Read these numbers with care.** The corpus is small and was written alongside the retrieval engine, so
scores near 1.0 show the gate works and regressions are caught, not that retrieval quality is proven on
real customer data. The local engine (BM25 + hashed character-trigram vectors) has no semantic embedding
model, so paraphrase-heavy queries will do worse than these queries suggest. Before launch, extend the set
with real, labelled customer-like documents (including image and audio), add nDCG@k, and re-set thresholds
from measured baselines. Grounded-answer faithfulness (LLM output checked against citations) is not yet
measured; only citation presence is.
