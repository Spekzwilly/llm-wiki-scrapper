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

### 2. Install the bridge server (one-time)

```bash
pip3 install pymupdf
bash bridge/install.sh
```

This registers the bridge as a macOS launchd service. After this, **no further commands are needed** — the server starts automatically at every login (including after a restart) and restarts itself if it ever crashes.

The bridge server runs on `localhost:7842` and requires:
- Python 3 (Homebrew: `/opt/homebrew/bin/python3`)
- `pymupdf` (`pip3 install pymupdf`) — for PDF text extraction
- `claude` CLI on your PATH
- `~/LLMwiki/` vault with the `llmwiki-ingest` skill installed

### 3. Verify it's running

```bash
curl http://localhost:7842/status
```

## Logs

Activity and errors are written to `~/LLMwiki/bridge.log`.

## Claude skills

Three skills work together inside the vault (invoke via `claude` from `~/LLMwiki`):

| Skill | Trigger | What it does |
|-------|---------|-------------|
| `/llmwiki-ingest` | Chrome extension save | Saves source, extracts concepts, writes wiki entries with tags |
| `/llmwiki-query` | Manual | Answers questions grounded in vault content with `[[wikilink]]` citations |
| `/llmwiki-lint` | Manual | Audits vault health — orphaned entries, missing pages, contradiction signals |

### Tag taxonomy

All wiki entries carry canonical YAML frontmatter tags:
`strategy` · `execution` · `communication` · `knowledge-management` · `frameworks` · `principles` · `mental-models`

Defined in `~/LLMwiki/CLAUDE.md §Tags`. Ingest assigns tags at creation; lint and query are tag-aware.

## Out of scope (v1)

YouTube transcripts, Safari/Firefox, multi-vault, cloud sync.
