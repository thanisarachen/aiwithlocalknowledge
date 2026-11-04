const storageKey = "local-gemma-chat-v1";
const conversation = document.getElementById("conversation");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");
const fileNotice = document.getElementById("file-notice");
const webToggle = document.getElementById("web-search-toggle");
const fileViewer = document.getElementById("file-viewer");
const viewerPdf = document.getElementById("viewer-pdf");
const viewerText = document.getElementById("viewer-text");
const viewerPagination = document.getElementById("viewer-pagination");
let viewerName = "";
let viewerPage = 1;
let viewerPageCount = 0;
let history = [];

function showPdfPage(page) {
  viewerPage = page;
  viewerPdf.src = `/api/pdf/${encodeURIComponent(viewerName)}/page/${page}`;
  document.getElementById("viewer-page-label").textContent = `Page ${page} of ${viewerPageCount}`;
  document.getElementById("viewer-previous").disabled = page <= 1;
  document.getElementById("viewer-next").disabled = page >= viewerPageCount;
}

document.getElementById("viewer-previous").addEventListener("click", () => showPdfPage(viewerPage - 1));
document.getElementById("viewer-next").addEventListener("click", () => showPdfPage(viewerPage + 1));

async function openFile(name) {
  const url = `/api/preview/${encodeURIComponent(name)}`;
  viewerName = name;
  document.getElementById("viewer-title").textContent = name;
  document.getElementById("viewer-download").href = `/api/files/${encodeURIComponent(name)}`;
  viewerPdf.hidden = true;
  viewerPdf.removeAttribute("src");
  viewerPagination.hidden = true;
  viewerText.hidden = true;
  viewerText.textContent = "";
  fileViewer.showModal();
  if (name.toLowerCase().endsWith(".pdf")) {
    try {
      const response = await fetch(`/api/pdf/${encodeURIComponent(name)}/metadata`);
      if (!response.ok) throw new Error("Could not open this PDF.");
      viewerPageCount = (await response.json()).pages;
      viewerPdf.hidden = false;
      viewerPagination.hidden = false;
      showPdfPage(1);
    } catch (error) {
      viewerText.hidden = false;
      viewerText.textContent = error.message;
    }
  } else {
    viewerText.hidden = false;
    viewerText.textContent = "Loading preview…";
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Could not open this document.");
      viewerText.textContent = await response.text();
    } catch (error) {
      viewerText.textContent = error.message;
    }
  }
}

document.getElementById("viewer-close").addEventListener("click", () => fileViewer.close());
fileViewer.addEventListener("close", () => viewerPdf.removeAttribute("src"));

try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
  if (Array.isArray(saved)) {
    history = saved.filter(m => m && ["user", "assistant"].includes(m.role) && typeof m.content === "string").slice(-40);
  }
} catch (_) { localStorage.removeItem(storageKey); }

function saveHistory() {
  history = history.slice(-40);
  try { localStorage.setItem(storageKey, JSON.stringify(history)); } catch (_) { /* Storage can be disabled. */ }
}

function linkify(container, value) {
  const pattern = /https?:\/\/[^\s<>"']+/gi;
  let last = 0;
  for (const match of value.matchAll(pattern)) {
    container.append(document.createTextNode(value.slice(last, match.index)));
    const raw = match[0];
    const urlText = raw.replace(/[.,!?;:)}\]]+$/, "");
    const trailing = raw.slice(urlText.length);
    try {
      const url = new URL(urlText);
      if (url.protocol === "http:" || url.protocol === "https:") {
        const link = document.createElement("a");
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = urlText;
        container.append(link);
      } else {
        container.append(document.createTextNode(urlText));
      }
    } catch (_) {
      container.append(document.createTextNode(urlText));
    }
    container.append(document.createTextNode(trailing));
    last = match.index + raw.length;
  }
  container.append(document.createTextNode(value.slice(last)));
}

function addMessage(role, content, sources = [], webSources = []) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "user" ? "YOU" : role === "error" ? "ERROR" : "GEMMA";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (role === "assistant") linkify(bubble, content);
  else bubble.textContent = content;
  item.append(label, bubble);
  if (role === "assistant" && Array.isArray(sources) && sources.length) {
    const note = document.createElement("div");
    note.className = "source-label";
    note.textContent = `Relevant documents: ${sources.join(", ")}`;
    item.append(note);
  }
  if (role === "assistant" && Array.isArray(webSources) && webSources.length) {
    const note = document.createElement("div");
    note.className = "source-label";
    note.append(document.createTextNode("Web results: "));
    linkify(note, webSources.join(" · "));
    item.append(note);
  }
  conversation.append(item);
  conversation.scrollTop = conversation.scrollHeight;
  return item;
}

function renderHistory() {
  conversation.replaceChildren();
  document.getElementById("clear-chat").hidden = history.length === 0;
  if (!history.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Ask about your trip or an uploaded document to get started.";
    conversation.append(empty);
    return;
  }
  for (const message of history) addMessage(message.role, message.content, message.sources, message.webSources);
}

document.getElementById("chat-form").addEventListener("submit", async event => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text || sendButton.disabled) return;
  if (conversation.querySelector(".empty-state")) conversation.replaceChildren();
  document.getElementById("clear-chat").hidden = false;
  addMessage("user", text);
  messageInput.value = "";
  messageInput.style.height = "";
  sendButton.disabled = true;
  sendButton.textContent = "Thinking…";
  const pending = addMessage("assistant", "Thinking…");
  try {
    const messages = [...history, { role: "user", content: text }].slice(-40);
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, web_search: webToggle.checked })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The request failed.");
    pending.remove();
    addMessage("assistant", data.answer, data.sources, data.web_sources);
    history.push({ role: "user", content: text }, { role: "assistant", content: data.answer,
                   sources: data.sources, webSources: data.web_sources });
    saveHistory();
  } catch (error) {
    pending.remove();
    addMessage("error", error.message || "Could not get a response.");
  } finally {
    sendButton.disabled = false;
    sendButton.textContent = "Send";
    messageInput.focus();
  }
});

messageInput.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    document.getElementById("chat-form").requestSubmit();
  }
});
messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 150)}px`;
});
document.getElementById("clear-chat").addEventListener("click", () => {
  history = [];
  saveHistory();
  renderHistory();
});

document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(button => {
    const active = button === tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.getElementById("chat-panel").hidden = tab.dataset.tab !== "chat";
  document.getElementById("documents-panel").hidden = tab.dataset.tab !== "documents";
  document.getElementById("page-title").textContent = tab.dataset.tab === "chat" ? "Trip Planning Assistant" : "Document collection";
  document.getElementById("page-description").textContent = tab.dataset.tab === "chat"
    ? "Plan trips with your preferences and uploaded travel documents."
    : "Upload and manage the files you want to keep with your collection.";
  if (tab.dataset.tab === "documents") loadFiles();
}));

function notice(text, isError = false) {
  fileNotice.textContent = text;
  fileNotice.classList.toggle("error", isError);
  fileNotice.hidden = false;
}

function formatSize(bytes) {
  return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB`;
}

async function loadFiles() {
  try {
    const response = await fetch("/api/files");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load files.");
    fileList.replaceChildren();
    document.getElementById("file-count").textContent = `${data.files.length} ${data.files.length === 1 ? "file" : "files"}`;
    if (!data.files.length) {
      const empty = document.createElement("p");
      empty.className = "files-empty";
      empty.textContent = "No files yet. Upload a document to start your collection.";
      fileList.append(empty);
    }
    for (const file of data.files) {
      const row = document.createElement("div"); row.className = "file-row";
      const meta = document.createElement("div"); meta.className = "file-meta";
      const title = document.createElement("a");
      title.href = `/api/preview/${encodeURIComponent(file.name)}`;
      title.textContent = file.name;
      title.addEventListener("click", event => { event.preventDefault(); openFile(file.name); });
      const size = document.createElement("small"); size.textContent = formatSize(file.size);
      const status = document.createElement("small");
      status.className = file.indexed ? "index-status" : "index-status missing";
      status.textContent = file.indexed ? `Indexed · ${file.chunks} ${file.chunks === 1 ? "chunk" : "chunks"}` : "Not indexed for chat";
      meta.append(title, size, status);
      if (!file.indexed) {
        const indexButton = document.createElement("button");
        indexButton.className = "file-action index";
        indexButton.type = "button";
        indexButton.textContent = "Index";
        indexButton.addEventListener("click", async () => {
          indexButton.disabled = true;
          indexButton.textContent = "Indexing…";
          try {
            const response = await fetch(`/api/files/${encodeURIComponent(file.name)}/index`, { method: "POST" });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Could not index file.");
            notice(`${file.name} indexed for chat.`);
            await loadFiles();
          } catch (error) { notice(error.message, true); indexButton.disabled = false; indexButton.textContent = "Index"; }
        });
        row.append(meta, indexButton);
      } else {
        row.append(meta);
      }
      const remove = document.createElement("button"); remove.className = "file-action delete";
      remove.type = "button"; remove.textContent = "Delete";
      remove.addEventListener("click", async () => {
        if (!confirm(`Delete ${file.name}?`)) return;
        try {
          const result = await fetch(`/api/files/${encodeURIComponent(file.name)}`, { method: "DELETE" });
          const data = await result.json();
          if (!result.ok) throw new Error(data.error || "Could not delete file.");
          notice(`${file.name} deleted.`);
          await loadFiles();
        } catch (error) { notice(error.message, true); }
      });
      row.append(remove);
      fileList.append(row);
    }
  } catch (error) { notice(error.message, true); }
}

document.getElementById("upload-form").addEventListener("submit", async event => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) return notice("Choose a file to upload.", true);
  if (file.size > 50 * 1024 * 1024) return notice("Files must be 50 MB or smaller.", true);
  const button = document.getElementById("upload-button");
  button.disabled = true;
  button.textContent = "Indexing…";
  try {
    const body = new FormData(); body.append("file", file);
    const response = await fetch("/api/files", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Upload failed.");
    notice(`Uploaded and indexed ${data.name}.`);
    fileInput.value = "";
    await loadFiles();
  } catch (error) { notice(error.message, true); }
  finally { button.disabled = false; button.textContent = "Upload"; }
});

renderHistory();

fetch("/api/config").then(response => response.json()).then(config => {
  document.getElementById("web-option").hidden = !config.web_search_available;
}).catch(() => { /* Keep optional web search hidden if configuration is unavailable. */ });
webToggle.addEventListener("change", () => {
  document.getElementById("mode-hint").textContent = webToggle.checked
    ? "Using qwen3:1.7b · Web search is on"
    : "Using gemma3:1b · Runs on this computer";
});
