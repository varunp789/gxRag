"""Gold evaluation corpus, one slice per modality that can be extracted locally.

Image (OCR) and audio (STT) need external providers and are reported as
``not_evaluated`` by the runner rather than silently skipped.
"""

from __future__ import annotations

WEB = {
    "web_zarnotide": ("Zarnotide program",
        "<html><body><h1>Zarnotide program</h1><p>Orbit Bio Labs develops Zarnotide, an inhibitor of the Kelvar pathway. "
        "Phase two trials of Zarnotide ran in Boston with Harborview Hospital. Zarnotide reduced tumour size in mice.</p>"
        "</body></html>"),
    "web_rivet": ("Rivet bond desk",
        "<html><body><p>Rivet Capital manages municipal bonds from its Frankfurt office. The Quantrix bond series matures "
        "in 2031. Rivet Capital reports quarterly yield figures to investors.</p></body></html>"),
    "web_logistics": ("Harbor logistics note",
        "<html><body><p>Northwind Freight ships refrigerated cargo through the port of Rotterdam. Northwind Freight "
        "signed a contract with Harborview Hospital for vaccine transport.</p></body></html>"),
}

CSV = {
    "csv_doses": ("Dose table", "compound,dose,species\nZarnotide,5mg,mouse\nKelvarin,9mg,rat\nPlacebo,0mg,mouse\n"),
    "csv_bonds": ("Bond ledger", "series,maturity,coupon\nQuantrix,2031,4.2\nBoreal,2028,3.1\nHalcyon,2035,5.0\n"),
}

PDF_TEXT = {
    "pdf_safety": ("Safety report",
        "Safety report. Adverse events for Zarnotide were mild. Nausea occurred in four percent of patients."),
    "pdf_audit": ("Audit memo",
        "Audit memo. Rivet Capital passed the annual compliance audit with no findings in Frankfurt."),
}

# query -> (mode, expected asset keys that must appear in the top-k)
QUERIES: list[tuple[str, str, set[str]]] = [
    ("Which company develops Zarnotide", "hybrid", {"web_zarnotide"}),
    ("Kelvar pathway inhibitor", "hybrid", {"web_zarnotide"}),
    ("Zarnotide trial in Boston", "vector", {"web_zarnotide"}),
    ("Quantrix bond maturity", "hybrid", {"web_rivet", "csv_bonds"}),
    ("refrigerated cargo Rotterdam", "hybrid", {"web_logistics"}),
    ("vaccine transport contract", "hybrid", {"web_logistics"}),
    ("Zarnotide adverse events nausea", "hybrid", {"pdf_safety"}),
    ("annual compliance audit Frankfurt", "hybrid", {"pdf_audit"}),
    ("Northwind Freight", "vector", {"web_logistics"}),
    ("Harborview Hospital", "hybrid", {"web_zarnotide", "web_logistics"}),
    ("Rivet Capital yield investors", "multimodal", {"web_rivet"}),
    ("compliance audit findings", "multimodal", {"pdf_audit"}),
    ("Zarnotide mice tumour", "vector", {"web_zarnotide"}),
    ("Kelvarin rat dose", "structured", {"csv_doses"}),
    ("Halcyon coupon", "structured", {"csv_bonds"}),
    ("Quantrix maturity", "structured", {"csv_bonds"}),
]

# Graph expansion: seed query -> asset that must be reached through a shared entity.
GRAPH_QUERIES: list[tuple[str, set[str]]] = [
    ("Zarnotide Boston trials", {"web_zarnotide", "web_logistics"}),  # via Harborview Hospital
]

# Entity / relation ground truth for graph correctness.
GRAPH_TRUTH = {
    "web_zarnotide": {"entities": {"Orbit Bio Labs", "Zarnotide", "Kelvar", "Harborview Hospital"},
                      "relations": {("Orbit Bio Labs", "Zarnotide"), ("Harborview Hospital", "Zarnotide")}},
    "web_rivet": {"entities": {"Rivet Capital", "Quantrix", "Frankfurt"},
                  "relations": {("Quantrix", "Rivet Capital"), ("Frankfurt", "Rivet Capital")}},
}

# Queries with no supporting evidence anywhere: retrieval must return nothing relevant.
NEGATIVE_QUERIES = ["quantum chromodynamics lattice", "recipe for sourdough bread"]


def build_pdf(text: str) -> bytes:
    """A minimal single-page text PDF (valid xref) readable by pypdf."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 50 700 Td ({escaped}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
