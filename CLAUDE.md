# LLMwiki Scrapper — Project Guide

## What this is

Chrome extension + Python bridge server that ingests web articles, PDFs, and YouTube videos into the user's Obsidian LLMwiki vault at `~/LLMwiki/`.

## Architecture

```
Browser (extension)  →  POST /ingest  →  bridge/server.py  →  claude -p /llmwiki-ingest  →  ~/LLMwiki/
```

### Extension (`extension/`)
- `manifest.json` — MV3, permissions: activeTab, scripting, storage, tabs; host: localhost:7842; includes custom icons (`icons/`)
- `content.js` — mouseup listener → tooltip → stores highlights in `chrome.storage.local` keyed by URL; responds to `getPageContent` message with `document.body.innerText`
- `background.js` — badge count management; refreshes on tab switch/load
- `popup.js` — loads tab metadata; detects PDF tabs via `isPdfUrl()` and YouTube tabs via `isYoutubeUrl()`; calls `getPageContent` for articles, sends `type:"pdf"` for PDFs, or `type:"youtube"` for YouTube → POST to bridge → polls `/status` every 2s
- `popup.html` — views: form, saving, processing, success, duplicate, error, no-content; `#highlights-section` hidden for PDFs and YouTube; `#pdf-badge` shown for PDFs; `#youtube-badge` shown for YouTube

### Bridge server (`bridge/`)
- `server.py` — Python stdlib HTTP server on `localhost:7842`
  - `POST /ingest` — accepts `{title, url, content, note, highlights}` for articles, `{title, url, note, type:"pdf"}` for PDFs, or `{title, url, note, type:"youtube"}` for YouTube; writes `~/LLMwiki/sources/<Title>.md`; spawns Claude in background thread
  - `GET /status` — returns `{state, title, concepts, error}` (idle/processing/done/error)
  - PDF extraction: `extract_pdf_text(url)` downloads PDF bytes via `urllib.request` and extracts text with `pymupdf`; returns 502 on failure
  - YouTube extraction: `extract_youtube_transcript(url)` fetches transcript via `youtube-transcript-api` (no API key), joins chunks as plain text, strips timestamps; returns 502 if no transcript available
  - Duplicate detection: checks existing sources files for matching `url:` frontmatter (type-agnostic)
  - Claude command: `claude --dangerously-skip-permissions -p "/llmwiki-ingest --source-file \"<path>\""` with `cwd=~/LLMwiki`; Claude timeout: 600s
- `requirements.txt` — pip dependencies (`pymupdf`, `youtube-transcript-api`)
- `install.sh` — installs launchd plist so bridge auto-starts on login
- `com.llmwiki.bridge.plist` — launchd service definition

### Vault layout (`~/LLMwiki/`)
- `sources/` — raw saved content as `.md` with YAML frontmatter (title, url, saved, type, personal-note, highlights); `type: article`, `type: pdf`, or `type: youtube`
- `bridge.log` — one line per ingestion event
- `CLAUDE.md` — vault governance: layer rules, operations, tag taxonomy (`## Tags`), prohibitions (`## Never do`)

### Claude skills (`~/.claude/skills/`)

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| `llmwiki-ingest` | Bridge server / direct | Save source, extract concepts, write tagged entries |
| `llmwiki-query` | Manual (`cd ~/LLMwiki && claude`) | Answer questions grounded in vault content with `[[wikilink]]` citations; optionally file answer as new entry |
| `llmwiki-lint` | Manual (`cd ~/LLMwiki && claude`) | Read-only vault health audit: orphaned entries, missing pages, contradiction signals |

**Tag taxonomy**: canonical tags (`strategy`, `execution`, `communication`, `knowledge-management`, `frameworks`, `principles`, `mental-models`) defined in `~/LLMwiki/CLAUDE.md §Tags`. All wiki entries carry YAML frontmatter `tags: [...]`.

## Key flows

**Save article**: popup opens → title/url auto-filled → user adds note → clicks Save → content.js returns `innerText` → bridge writes sources file → responds 200 → Claude processes async → macOS notification fires → popup polls done

**Save PDF**: popup detects `.pdf` URL → hides highlights, shows PDF badge → user adds note → clicks Save → bridge downloads + extracts PDF text via pymupdf → writes sources file with `type: pdf` → Claude processes async → macOS notification fires

**Save YouTube**: popup detects `youtube.com/watch` URL → hides highlights, shows YT badge → user adds note → clicks Save → bridge fetches transcript via `youtube-transcript-api` (plain text, no timestamps) → writes sources file with `type: youtube` → Claude processes async → macOS notification fires; returns 502 if no transcript available

**Highlights**: select text on article page → tooltip appears → click → stored in chrome.storage → shown in popup → sent as array in `highlights:` frontmatter (not available for PDFs or YouTube)

## Spectra

This project uses Spectra for Spec-Driven Development. Specs in `openspec/specs/`, change proposals in `openspec/changes/`.

## Coding guidelines

Always apply `/karpathy-guidelines` when writing or reviewing code:
- Make surgical changes — don't touch what isn't broken
- No abstractions beyond what the task requires
- Surface assumptions explicitly
- Define verifiable success criteria before implementing
