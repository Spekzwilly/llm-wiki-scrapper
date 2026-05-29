## Why

Capturing knowledge from articles requires opening a terminal and running a CLI skill — a friction-heavy context switch that breaks reading flow and makes consistent capture unlikely. This extension closes the loop: find an article, click once, wiki updated automatically.

## What Changes

- New Chrome extension (Manifest V3) with popup UI for article capture
- New local Python bridge server that receives extension payloads and orchestrates ingestion
- New macOS launchd service that keeps the bridge server running at login
- Updated `llmwiki-ingest` skill to read from local sources files instead of fetching URLs
- Highlights captured during reading are saved as extraction signal for Claude

## Capabilities

### New Capabilities

- `chrome-extension`: Manifest V3 extension with content script (selection → highlight tooltip), popup UI (title, note, highlights, save), and background script (badge management)
- `bridge-server`: Local Python HTTP server on localhost:7842 — receives POST /ingest, deduplicates by URL, writes sources file, triggers Claude CLI, sends macOS notification, logs activity
- `launchd-service`: macOS launchd plist that auto-starts the bridge server at login and keeps it running

### Modified Capabilities

- `llmwiki-ingest`: Updated to accept a `--source-file` argument (reads local file instead of fetching URL) and use highlights from frontmatter as extraction priority signal

## Impact

- Affected code: `~/.claude/skills/llmwiki-ingest/SKILL.md`, `~/.claude/skills/llmwiki-ingest/REFERENCE.md`
- New files: `extension/manifest.json`, `extension/content.js`, `extension/popup.html`, `extension/popup.js`, `extension/background.js`, `bridge/server.py`, `bridge/com.llmwiki.bridge.plist`
- Vault dependency: `~/LLMwiki/sources/` must exist (already set up)
- External dependency: `claude` CLI must be on PATH for bridge server to trigger ingestion
