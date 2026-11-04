# AI with Local Knowledge

A small, private document Q&A app. Upload PDF, DOCX, Markdown, or plain text files and ask questions in your browser. SQLite full-text search finds relevant passages; a local [Ollama](https://ollama.com/) model writes an answer with numbered source references. Documents, the index, and the model stay on your computer.

## Quick start

Requires Python 3.9+ and Ollama.

From the project folder (after cloning the repository or extracting the ZIP):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3.5:4b
ollama serve
```

If the Ollama app is already running, skip `ollama serve`. In another terminal, from the same folder:

```bash
source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Add documents, then ask a question. The status indicator shows whether Ollama and the configured model are ready.

To use another installed model, set `OLLAMA_MODEL` before starting the server. Set `OLLAMA_URL` to point to a different Ollama server, or `KNOWLEDGE_DB` to choose another SQLite database path.

## Notes

- Files are indexed locally in `data/knowledge.db`. Removing a document deletes its indexed text. Original uploads are not retained.
- Each file is limited to 20 MB. Scanned PDFs need OCR first; this app extracts embedded text only.
- Search uses SQLite FTS5 keyword matching. Exact wording in your question helps retrieval; answers may be incomplete if no relevant passage is found.
- The server binds to localhost in the command above. Do not expose it publicly without adding authentication and upload controls.
