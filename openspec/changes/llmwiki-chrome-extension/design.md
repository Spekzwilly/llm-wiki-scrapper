## Context

The user has a working LLMwiki vault at `~/LLMwiki/` with an existing `llmwiki-ingest` skill that reads sources files and extracts atomic concepts into wiki entries. The current ingestion flow requires opening a terminal and running the skill manually with a URL. The goal is to eliminate that friction entirely via a Chrome extension backed by a local bridge server.

A prototype UI has been validated (`prototype.html` in repo root) — three variants tested, design direction confirmed. The bridge server and extension are new; the skill is updated but not replaced.

## Goals / Non-Goals

**Goals:**
- Zero-terminal article capture: click extension → wiki updated automatically
- Optional text highlighting during reading that guides Claude's extraction
- Reliable local sources file preservation (even if Claude fails, raw content is saved)
- Auto-start bridge server on Mac login via launchd

**Non-Goals:**
- YouTube transcript extraction (deferred)
- PDF content extraction (deferred)
- Safari or Firefox support
- Multi-vault support
- Publishing to Chrome Web Store (unpacked extension only)
- Cloud sync or remote bridge

## Decisions

### Bridge over Native Messaging

**Decision:** Use a local HTTP server (Python, localhost:7842) rather than Chrome Native Messaging.

Native messaging requires registering a manifest with Chrome and is harder to debug. An HTTP server on localhost is simpler to build, easy to curl-test, and straightforward for a non-developer user to understand. Security risk is acceptable for a single-user local tool.

### Python for bridge server

**Decision:** Python over Node.js for the bridge server.

Python ships with macOS, requires no package manager setup, and `http.server` + `subprocess` cover all needs. Node would require npm and a runtime version decision. Lower setup friction for the user.

### Non-blocking Claude trigger

**Decision:** Bridge server responds 200 to the extension immediately after writing the sources file, then triggers Claude in a background subprocess.

This keeps the extension popup responsive. The user gets instant feedback ("Saving…" → closes) and the macOS notification arrives when ingestion actually completes. If Claude fails, the sources file is already written and content is preserved.

### Sources file as the handoff unit

**Decision:** The bridge writes the sources file first; Claude reads from it. The extension never talks to Claude directly.

This decouples capture from ingestion. Even if Claude is unavailable, content is saved. The skill is invoked with a `--source-file` path so it reads local content instead of fetching the URL — no token spend on content extraction.

### Highlights as frontmatter YAML

**Decision:** Store highlights as a YAML list under `highlights:` in the sources file frontmatter.

Frontmatter is machine-readable, human-readable, and doesn't pollute the article body. The skill reads the highlights list before processing and uses them to weight concept extraction.

### Duplicate detection by URL

**Decision:** Bridge server checks `url:` frontmatter across all files in `~/LLMwiki/sources/` before writing. If a match is found, it returns a 409 and the extension shows "Already saved."

Prevents duplicate sources files from the same article. Fast enough for a personal vault (< 1000 files).

## Implementation Contract

### Bridge Server

**Behavior:** A Python HTTP server listens on `localhost:7842`. Accepts `POST /ingest` with JSON body. Returns immediately after writing the sources file. Triggers Claude in background. Sends macOS notification on completion.

**Request shape:**
```json
{
  "title": "string",
  "url": "string",
  "content": "string",
  "highlights": ["string"],
  "note": "string"
}
```

**Response shapes:**
- `200 OK` — sources file written, Claude triggered in background
- `409 Conflict` — URL already exists in sources/
- `400 Bad Request` — missing required fields (title, url, content)

**Sources file written to:** `~/LLMwiki/sources/<Title Case Title>.md`

**Claude trigger command:** `claude --print "/llmwiki-ingest --source-file <path>"` run as background subprocess

**Notification:** `osascript -e 'display notification "N concepts added" with title "LLMwiki"'` after Claude subprocess exits

**Log file:** `~/LLMwiki/bridge.log` — append-only, one line per ingestion with timestamp, title, URL, concept count

**Acceptance criteria:**
- `curl -X POST localhost:7842/ingest -H 'Content-Type: application/json' -d '{...}'` returns 200 and creates sources file
- Same URL posted twice returns 409, no duplicate file
- Sources file contains correct frontmatter and article body
- macOS notification appears after Claude completes
- Bridge auto-starts after `launchctl load` of the plist

### Chrome Extension

**Behavior:** Content script listens for `mouseup` events on the page. When selection is ≥ 10 chars and outside the extension popup, shows a floating "Add to Highlights" button above the selection. Clicking it stores the highlight in `chrome.storage.local` keyed by URL. Extension icon badge shows highlight count.

Popup reads current tab's title and URL via `chrome.tabs`, loads stored highlights for that URL, renders them with × remove buttons. Personal Note textarea is optional. Save button POSTs to bridge server. Status transitions: idle → saving → success/error.

**Content script interface:** Writes to `chrome.storage.local` under key `highlights_<url>` as a JSON array of strings.

**Popup to bridge:** Single `fetch('http://localhost:7842/ingest', { method: 'POST', body: JSON.stringify({...}) })`

**Error state trigger:** Any non-200 response or network error (ECONNREFUSED) → shows "Bridge server not running"

**Acceptance criteria:**
- Selecting text on any article page shows the tooltip
- Highlights persist across popup open/close
- Badge updates when highlights are added/removed
- Save → saving state → macOS notification → success state in popup (on re-open)
- 409 response → "Already saved" shown instead of success

### llmwiki-ingest skill update

**Behavior:** When invoked with `--source-file <path>`, reads the local file instead of fetching a URL. Extracts `highlights` from frontmatter and uses them as weighted signal: concepts that appear in or are closely related to highlighted passages are extracted first, with richer "When to apply" sections.

**Acceptance criteria:**
- `claude --print "/llmwiki-ingest --source-file ~/LLMwiki/sources/Article.md"` produces wiki entries without WebFetch
- Concepts linked to highlighted passages appear in the output
- Existing deduplication and enrichment behavior unchanged

## Risks / Trade-offs

- **Claude CLI path** → Bridge server must find `claude` on PATH. Mitigation: use `which claude` at server startup and fail fast with a clear log message if not found.
- **Bridge server not running** → Extension shows clear error state. Mitigation: error message says exactly "Bridge server not running" so user knows what to fix.
- **Long ingestion time** → Claude can take 30–60s. Mitigation: non-blocking design means extension popup closes immediately; user is notified via macOS notification when done.
- **Large articles** → Very long articles may hit Claude context limits. Mitigation: bridge server truncates content to 50,000 chars before writing to sources file (covers 99% of articles).
