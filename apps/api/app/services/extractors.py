"""Provider-backed extraction with source-evidence preservation."""

from __future__ import annotations

import base64
import csv
import io
import subprocess
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import httpx
import pandas as pd
from pypdf import PdfReader

from app.core.config import settings


@dataclass(frozen=True)
class ExtractedContent:
    text: str
    rows: list[dict[str, str]]
    warnings: list[str]
    evidence: list[dict[str, str]]
    provider: str


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def read_source(location: str, content_base64: str | None = None) -> bytes:
    if content_base64:
        return base64.b64decode(content_base64, validate=True)
    if location.startswith(("http://", "https://")):
        response = httpx.get(location, follow_redirects=True, timeout=30)
        response.raise_for_status()
        return response.content
    if location.startswith("file://"):
        return Path(location.removeprefix("file://")).read_bytes()
    raise ValueError("No readable source content is available. Upload bytes or provide an HTTP(S) URL.")


def extract_pdf(raw: bytes) -> ExtractedContent:
    reader = PdfReader(io.BytesIO(raw))
    pages = [page.extract_text() or "" for page in reader.pages]
    return ExtractedContent(
        text="\n\n".join(pages).strip(), rows=[], warnings=[],
        evidence=[{"page": str(index + 1)} for index in range(len(pages))], provider="pypdf",
    )


def extract_spreadsheet(raw: bytes, file_name: str) -> ExtractedContent:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    else:
        frame = pd.read_excel(io.BytesIO(raw))
        rows = [{key: "" if pd.isna(value) else str(value) for key, value in row.items()} for row in frame.to_dict("records")]
    text = "\n".join(" | ".join(f"{key}: {value}" for key, value in row.items()) for row in rows)
    return ExtractedContent(text=text, rows=rows, warnings=[], evidence=[{"row": str(index + 1)} for index in range(len(rows))], provider="csv/pandas")


def extract_web(raw: bytes) -> ExtractedContent:
    parser = _TextParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return ExtractedContent(text="\n".join(parser.parts), rows=[], warnings=[], evidence=[{"section": "document"}], provider="html.parser")


def extract_image(raw: bytes) -> ExtractedContent:
    with tempfile.NamedTemporaryFile(suffix=".img") as input_file, tempfile.NamedTemporaryFile(suffix=".txt") as output_file:
        input_file.write(raw)
        input_file.flush()
        command = ["tesseract", input_file.name, output_file.name.removesuffix(".txt")]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=60)
        except FileNotFoundError as error:
            raise RuntimeError("OCR provider unavailable: install the tesseract binary.") from error
        text = Path(output_file.name).read_text(errors="replace")
    return ExtractedContent(text=text, rows=[], warnings=[], evidence=[{"region": "full-image"}], provider="tesseract")


def extract_audio(raw: bytes) -> ExtractedContent:
    if not settings.openai_api_key:
        raise RuntimeError("STT provider unavailable: set GXRAG_OPENAI_API_KEY.")
    response = httpx.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        files={"file": ("audio.bin", raw), "model": (None, "gpt-4o-mini-transcribe")}, timeout=120,
    )
    response.raise_for_status()
    text = response.json()["text"]
    return ExtractedContent(text=text, rows=[], warnings=[], evidence=[{"timestamp": "0"}], provider="openai:gpt-4o-mini-transcribe")


def extract(asset_type: str, raw: bytes, file_name: str) -> ExtractedContent:
    if asset_type == "document":
        return extract_pdf(raw)
    if asset_type == "spreadsheet":
        return extract_spreadsheet(raw, file_name)
    if asset_type == "web_page":
        return extract_web(raw)
    if asset_type == "image":
        return extract_image(raw)
    if asset_type == "audio":
        return extract_audio(raw)
    raise ValueError(f"Unsupported asset type: {asset_type}")
