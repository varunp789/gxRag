# Evaluation dataset and release gates

Maintain a versioned gold set for PDF, spreadsheet, web, image OCR, and audio STT sources. Each item includes source evidence, expected extraction text, expected entities/relations, and relevance-labelled retrieval queries.

Release gates: extraction exact-match or field-level F1, retrieval nDCG@8, graph edge precision/recall, and grounded-answer citation coverage. Run the set before each release and record the scores with the release candidate.
