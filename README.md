# LLMwiki Chrome Extension

A personal Chrome extension that saves articles to your [LLMwiki](https://obsidian.md/) vault with one click. Highlight passages, add a personal note, and click Save — Claude extracts concepts and updates your wiki automatically, with a macOS notification when it's done.

## How it works

```
Chrome Extension  →  Bridge Server (localhost:7842)  →  ~/LLMwiki/sources/
                                                      →  claude --dangerously-skip-permissions -p /llmwiki-ingest
                                                      →  macOS notification
```

1. Click the extension icon on any article page
2. Optionally highlight passages and add a personal note
3. Click **Save** — the bridge server writes a sources file and triggers Claude in the background
4. A macOS notification confirms how many concepts were added or enriched

## Project structure

```
bridge/
  server.py              # Python HTTP server on localhost:7842
  install.sh             # Registers bridge as a launchd service (auto-starts at login)
  com.llmwiki.bridge.plist

extension/
  manifest.json          # Chrome extension manifest (MV3)
  content.js             # Injects into pages — captures article text and highlights
  background.js          # Service worker — manages highlight badge
  popup.html / popup.js  # Extension UI
```

## Setup

### 1. Load the Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder

### 2. Start the bridge server

**Manually (one-off):**
```bash
python3 bridge/server.py
```

**Auto-start at login (recommended):**
```bash
bash bridge/install.sh
```

The bridge server runs on `localhost:7842` and requires:
- Python 3 (stdlib only — no pip installs needed)
- `claude` CLI on your PATH
- `~/LLMwiki/` vault with the `llmwiki-ingest` skill installed

### 3. Verify it's running

```bash
curl http://localhost:7842/status
```

## Logs

Activity and errors are written to `~/LLMwiki/bridge.log`.

## Out of scope (v1)

YouTube transcripts, PDFs, Safari/Firefox, multi-vault, cloud sync.
