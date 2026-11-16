# AI Personalized Trip Planning Assistant

A browser-based travel planning prototype using a local language model and uploaded travel documents.

## Current demo

The latest application is in **[trip-planner-github-source](trip-planner-github-source/)**. It supports document uploads and previews, source-backed chat, saved trip-planning prompts, hotel comparisons, budget reviews and formatted responses.

Follow the **[setup and usage instructions](trip-planner-github-source/README.md)** to install Python dependencies and the required Ollama models, then run the app locally:

```bash
cd trip-planner-github-source
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
ollama pull qwen3.5:4b
ollama pull nomic-embed-text
python3 app.py
```

Ollama must be running. On Windows, activate with `.venv\Scripts\activate`. Open http://127.0.0.1:5000/ after starting the app.

The public copy starts with an empty document collection. Upload your own trip brief, budget and destination references. Personal documents, credentials and local indexes are excluded. Generated plans are drafts; prices, availability and feasibility need verification.

This repository contains runnable source code, not a hosted public website. The older root-level `app.py` is retained as an earlier document-Q&A prototype; use the folder above for the current trip planner.

## Project

**Group:** Latte and chen*2

- Thanisara Chen (Matoom)
- Xiaotong Chen (Sunny)
- Nop Skowratananont (Latte)

See [research sources](trip-planner-github-source/SOURCES.md) for project background. Live booking, map routing, weather feeds and multi-user collaboration remain future extensions.
