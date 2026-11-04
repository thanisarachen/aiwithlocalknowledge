# AI Personalized Trip Planning Assistant

A local Flask app that plans trips using your preferences and answers questions about uploaded travel documents. Chat uses Ollama's `gemma3:1b`; document search uses local `nomic-embed-text` embeddings. The model and document index run on this computer. Five suggested research PDFs and their original links are listed in [SOURCES.md](SOURCES.md). Download and upload them after setup; this GitHub package contains source code only.

## Setup

Install [Ollama](https://ollama.com/download), then pull both models:

```bash
ollama pull gemma3:1b
ollama pull nomic-embed-text
```

Ollama normally starts its local service automatically. If needed, start it in another terminal with `ollama serve`.

From this project folder, create a Python environment and run Flask:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open <http://127.0.0.1:5000/> in a browser. Stop Flask with Ctrl+C. If port 5000 is in use (as it is on this Mac because of AirPlay), run `PORT=5001 python3 app.py` and open <http://127.0.0.1:5001/>.

## Use

1. Open **Document collection** and upload a PDF, DOCX, TXT, or Markdown file, up to 50 MB. The app extracts its text, divides it into chunks, and asks Ollama for embeddings. Wait for **Uploaded and indexed** before chatting about it.
2. Open **Chat** and ask about a document, or ask for an itinerary with a destination, dates, budget, interests, and pace. The app retrieves relevant document excerpts and gives them to Gemma with your question. Answers show the document names that were retrieved. Ask “What are the papers in my document collection?” to see every uploaded filename, index status, chunk count, and opening excerpt.
3. If a file shows **Not indexed for chat**, select **Index** beside it to add it to the searchable collection.
4. Click a green filename to preview its contents. PDFs open as rendered pages with **Previous** and **Next** controls. TXT, Markdown, and DOCX files open as text. Use **Download file** in the preview to save the original.

Uploaded files are in `data/uploads/`; their local search data is in `data/index/`. Deleting a file removes its index. Browser chat history is stored in local storage and sent with each question; **Clear chat** removes it. HTTP and HTTPS links in replies open in a new tab.

The server listens only on `127.0.0.1`. Browser JavaScript never calls Ollama directly. Scanned or image-only PDFs need OCR before upload, because this app extracts embedded text. Very long documents may exceed the local demo's indexing limit.

## Optional web search

For current travel information, create an Ollama API key using the [Ollama web search instructions](https://docs.ollama.com/capabilities/web-search) and pull the lab's web-enabled model:

```bash
ollama pull qwen3:1.7b
```

Set `OLLAMA_API_KEY` in the Flask server's environment, then restart the app. The **Use web search** checkbox appears only when a key is set. When selected, the app sends that question to Ollama's hosted web search API and uses `qwen3:1.7b` to answer with search results. Leave it off to keep chat and document retrieval local. Never put the key in source code or commit it to Git.
