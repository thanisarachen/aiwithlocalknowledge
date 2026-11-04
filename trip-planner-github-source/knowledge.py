"""Local text extraction, Ollama embeddings, and small-file semantic search."""

import json
import math
import os
import re
import urllib.error
import urllib.request
import uuid
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
INDEX_DIR = BASE_DIR / "data" / "index"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
EMBED_MODEL = "nomic-embed-text"
OLLAMA_BASE = "http://127.0.0.1:11434"
MAX_TEXT_CHARS = 350_000
MAX_CHUNKS = 350


class DocumentError(Exception):
    """An uploaded file cannot be indexed."""


class OllamaError(Exception):
    """A local Ollama request failed."""


def ollama_post(endpoint, payload, timeout=180):
    request = urllib.request.Request(
        OLLAMA_BASE + endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            body = json.load(exc)
            detail = body.get("error", "") if isinstance(body, dict) else ""
        except (ValueError, UnicodeError):
            detail = ""
        raise OllamaError(f"Ollama returned an error: {detail or exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise OllamaError("Could not reach Ollama. Check that it is running and the required models are installed.") from exc
    except (ValueError, UnicodeError, OSError) as exc:
        raise OllamaError("Ollama returned a response that could not be read.") from exc


def extract_segments(content, suffix):
    """Return text segments with optional PDF page numbers."""
    try:
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(content), strict=False)
            if reader.is_encrypted and not reader.decrypt(""):
                raise DocumentError("Password-protected PDFs cannot be indexed.")
            segments = []
            length = 0
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                length += len(text)
                if length > MAX_TEXT_CHARS:
                    raise DocumentError("This document has too much text to index in the local demo.")
                if text.strip():
                    segments.append({"text": text, "page": page_number})
            return segments
        if suffix == ".docx":
            document = Document(BytesIO(content))
            parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            text = "\n".join(parts)
        else:
            text = content.decode("utf-8-sig", errors="replace")
        if len(text) > MAX_TEXT_CHARS:
            raise DocumentError("This document has too much text to index in the local demo.")
        return [{"text": text, "page": None}]
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("This file could not be read. Check that it is a valid, unprotected document.") from exc


def chunk_segments(segments):
    chunks = []
    for segment in segments:
        text = re.sub(r"\s+", " ", segment["text"]).strip()
        start = 0
        while start < len(text):
            end = min(start + 1000, len(text))
            if end < len(text):
                space = text.rfind(" ", start + 650, end)
                if space > start:
                    end = space
            piece = text[start:end].strip()
            if piece:
                chunks.append({"text": piece, "page": segment["page"]})
                if len(chunks) > MAX_CHUNKS:
                    raise DocumentError("This document is too long to index in the local demo.")
            if end == len(text):
                break
            start = max(end - 150, start + 1)
    if not chunks:
        raise DocumentError("No extractable text was found. Scanned PDFs need OCR before upload.")
    return chunks


def embed_texts(texts):
    vectors = []
    for offset in range(0, len(texts), 16):
        batch = texts[offset:offset + 16]
        result = ollama_post("/api/embed", {"model": EMBED_MODEL, "input": batch, "truncate": False})
        embeddings = result.get("embeddings") if isinstance(result, dict) else None
        if not isinstance(embeddings, list) or len(embeddings) != len(batch):
            raise OllamaError("Ollama returned invalid embeddings.")
        for embedding in embeddings:
            if not isinstance(embedding, list) or not embedding:
                raise OllamaError("Ollama returned invalid embeddings.")
            try:
                values = [float(value) for value in embedding]
                magnitude = math.sqrt(sum(value * value for value in values))
                if not math.isfinite(magnitude) or magnitude == 0:
                    raise ValueError("zero or invalid vector")
                vectors.append([value / magnitude for value in values])
            except (TypeError, ValueError) as exc:
                raise OllamaError("Ollama returned invalid embeddings.") from exc
    return vectors


def index_path(name):
    return INDEX_DIR / f"{name}.json"


def read_index(name):
    path = index_path(name)
    source = UPLOAD_DIR / name
    if not source.is_file() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("name") != name or data.get("size") != source.stat().st_size or data.get("model") != EMBED_MODEL:
            return None
        if not isinstance(data.get("chunks"), list):
            return None
        return data
    except (OSError, ValueError, AttributeError):
        return None


def index_document(name, content):
    chunks = chunk_segments(extract_segments(content, Path(name).suffix.lower()))
    vectors = embed_texts([chunk["text"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["vector"] = vector
    data = {"name": name, "size": len(content), "model": EMBED_MODEL, "chunks": chunks}
    destination = index_path(name)
    temporary = INDEX_DIR / f".{uuid.uuid4().hex}.tmp"
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return len(chunks)


def search_documents(query, limit=4):
    all_chunks = []
    for source in UPLOAD_DIR.iterdir():
        if not source.is_file():
            continue
        index = read_index(source.name)
        if index:
            all_chunks.extend((source.name, chunk) for chunk in index["chunks"])
    if not all_chunks:
        return []
    query_vector = embed_texts([query])[0]
    matches = []
    for name, chunk in all_chunks:
        vector = chunk.get("vector")
        if isinstance(vector, list) and len(vector) == len(query_vector):
            score = sum(a * b for a, b in zip(query_vector, vector))
            matches.append((score, name, chunk))
    matches.sort(reverse=True, key=lambda item: item[0])
    return [{"name": name, "page": chunk.get("page"), "text": chunk["text"], "score": score}
            for score, name, chunk in matches[:limit] if score >= 0.2]


def web_search(query, api_key):
    """Search through Ollama's hosted API only when a user opts in."""
    request = urllib.request.Request(
        "https://ollama.com/api/web_search",
        data=json.dumps({"query": query, "max_results": 5}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise OllamaError(f"Web search failed (HTTP {exc.code}). Check your Ollama API key.") from exc
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        raise OllamaError("Web search is unavailable right now.") from exc
    raw_results = result.get("results") if isinstance(result, dict) else None
    if not isinstance(raw_results, list):
        raise OllamaError("Web search returned an invalid response.")
    results = []
    for item in raw_results[:5]:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            continue
        results.append({
            "title": str(item.get("title", ""))[:200],
            "url": url[:1000],
            "content": str(item.get("content", ""))[:2000],
        })
    return results
