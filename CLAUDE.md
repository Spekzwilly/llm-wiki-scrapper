# LLMwiki Scrapper — Project Guide

## What this is

Chrome extension + Python bridge server that ingests web articles into the user's Obsidian LLMwiki vault at `~/LLMwiki/`.

## Architecture

```
Browser (extension)  →  POST /ingest  →  bridge/server.py  →  claude -p /llmwiki-ingest  →  ~/LLMwiki/
```

### Extension (`extension/`)
- `manifest.json` — MV3, permissions: activeTab, scripting, storage, tabs; host: localhost:7842
- `content.js` — mouseup listener → tooltip → stores highlights in `chrome.storage.local` keyed by URL; responds to `getPageContent` message with `document.body.innerText`
- `background.js` — badge count management; refreshes on tab switch/load
- `popup.js` — loads tab metadata + stored highlights; calls `getPageContent` → POST to bridge → polls `/status` every 2s
- `popup.html` — views: form, saving, processing, success, duplicate, error, no-content

### Bridge server (`bridge/`)
- `server.py` — Python stdlib HTTP server on `localhost:7842`
  - `POST /ingest` — validates body `{title, url, content, note, highlights}`, writes `~/LLMwiki/sources/<Title>.md`, spawns Claude in background thread
  - `GET /status` — returns `{state, title, concepts, error}` (idle/processing/done/error)
  - Duplicate detection: checks existing sources files for matching `url:` frontmatter
  - Claude command: `claude --dangerously-skip-permissions -p "/llmwiki-ingest --source-file <path>"` with `cwd=~/LLMwiki`
- `install.sh` — installs launchd plist so bridge auto-starts on login
- `com.llmwiki.bridge.plist` — launchd service definition

### Vault layout (`~/LLMwiki/`)
- `sources/` — raw saved articles as `.md` with YAML frontmatter (title, url, saved, type, personal-note, highlights)
- `bridge.log` — one line per ingestion event

## Key flows

**Save article**: popup opens → title/url auto-filled → user adds note → clicks Save → content.js returns `innerText` → bridge writes sources file → responds 200 → Claude processes async → macOS notification fires → popup polls done

**Highlights**: select text → tooltip appears → click → stored in chrome.storage → shown in popup → sent as array in `highlights:` frontmatter

## Spectra

This project uses Spectra for Spec-Driven Development. Specs in `openspec/specs/`, change proposals in `openspec/changes/`.

## Coding guidelines

Always apply `/karpathy-guidelines` when writing or reviewing code:
- Make surgical changes — don't touch what isn't broken
- No abstractions beyond what the task requires
- Surface assumptions explicitly
- Define verifiable success criteria before implementing
