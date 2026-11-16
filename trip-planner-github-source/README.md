# AI Personalized Trip Planning Assistant

A local Flask app that drafts trips using personal preferences and uploaded travel references. Chat defaults to Ollama's `qwen3.5:4b`; document search uses local `nomic-embed-text` embeddings. Set `TRIP_MODEL` to use another installed model. The model and document index run on this computer.

This public source copy starts with an empty document collection. Upload your own trip brief, budget and travel reference files before asking for a plan. Personal travel documents, flight screenshots, reviewed profiles and search indexes are not included. The three saved prompts read the details from your uploaded documents rather than containing a traveler's personal information.

The local project demonstration used a dated Tokyo reference collection. That private collection is not bundled here; the app does not include live hotel inventory or automatically download destination data.

## Setup

Install [Ollama](https://ollama.com/download), then pull both models:

```bash
ollama pull qwen3.5:4b
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

On Windows, activate with `.venv\Scripts\activate` instead. Open <http://127.0.0.1:5000/> in a browser. Stop Flask with Ctrl+C. If port 5000 is in use (for example, by another application), run `PORT=5001 python3 app.py` and open <http://127.0.0.1:5001/>.

## Use

1. Open **Document collection** and upload a PDF, DOCX, TXT, or Markdown file, up to 50 MB. The app extracts its text, divides it into chunks, and asks Ollama for embeddings. Wait for **Uploaded and indexed** before chatting about it.
2. Open **Chat** and ask about a document, or ask for an itinerary with a destination, dates, budget, interests, and pace. The app gives the active trip collection and relevant excerpts to the model. Answers show clickable document references. Ask “What files are in my document collection?” to see every uploaded filename and index status. After uploading your documents, choose **Plan my Japan trip**, **Compare hotels**, or **Review my budget** to fill the detailed saved prompt, then press **Enter** or **Send**. **Shift+Enter** adds a new line. The trip-plan prompt covers the itinerary, transportation, meals, activities and budget; hotel recommendations are requested separately by **Compare hotels**. Prompts can be edited before sending.
3. If a file shows **Not indexed for chat**, select **Index** beside it to add it to the searchable collection.
4. Click a green filename to preview its contents. PDFs open as rendered pages with **Previous** and **Next** controls. TXT, Markdown, and DOCX files open as text. Use **Download file** in the preview to save the original.

Uploaded files are in `data/uploads/`; their local search data is in `data/index/`. Deleting a file removes its index. Browser chat history is stored in local storage and sent with each question; **Clear chat** removes it. HTTP and HTTPS links in replies open in a new tab.

Assistant replies, including saved history, display Markdown headings, bold text, lists and tables. The browser uses a locally bundled copy of [markdown-it 15.0.3](https://github.com/markdown-it/markdown-it) with its MIT license in `static/vendor/`; no CDN is needed. Raw HTML and images are disabled, and only HTTP/HTTPS links are allowed. Wide comparison tables scroll inside the reply on small screens.

The server listens only on `127.0.0.1`. Browser JavaScript never calls Ollama directly. Scanned or image-only PDFs need OCR before upload, because this app extracts embedded text. Very long documents may exceed the local demo's indexing limit. Full plans may take several minutes on a local model. Generated answers remain drafts: source retrieval does not guarantee that every date, fare, route, or budget calculation in an answer is correct.

## Active trip references

The optional local `data/trip_context.json` manifest lists `profiles`, `references`, `checked_on`, and `excluded_from_trip_context`. Files must exist in `data/uploads/` and have valid indexes. Broad planning requests use the active collection with complete reference cards. Focused first questions use up to 12 relevant excerpts plus the reviewed personal facts. Additional uploads use semantic search.

An optional `reviewed_profile` stores manually reviewed personal facts and source-file hashes. `planning_facts.py` calculates weekdays, hotel nights, personal budget totals and the equal-share room allowance from that data. This factual digest replaces repeated raw-brief prose in the model prompt, while the original files remain cited and previewable. Changed or deleted source files disable those calculated reminders until the reviewed profile is updated. They inform the model; they are not a complete validation of its answer. New instructions in chat can revise the trip.

For a useful trip collection, upload a brief with dates, party size, flights, interests and pace; a budget with clear personal/shared units; and destination references covering hotels, transport, restaurants and activities. Include source URLs, research dates and uncertainty in the references. Configure a local manifest if the complete collection should accompany every chat request. Keep API keys and private travel documents out of Git.

The prototype supports document-backed planning and follow-up questions. Live hotel inventory, reservation submission, weather feeds, map routing, booking tracking and multi-user collaboration still need separate integrations.

Run focused checks with `python -m unittest -v test_trip_context.py`.

## Optional web search

For current travel information, create an Ollama API key using the [Ollama web search instructions](https://docs.ollama.com/capabilities/web-search). Set `OLLAMA_API_KEY` in the Flask server's environment, then restart the app. The **Use web search** checkbox appears only when a key is set. When selected, the app sends recent question text to Ollama's hosted search API and adds the results to the model's context. `TRIP_WEB_MODEL` can select a different installed model; it defaults to `TRIP_MODEL`. Leave search off to keep chat and document retrieval local. Never put the key in source code or commit it to Git. Search results are not confirmed reservations or live booking inventory.
