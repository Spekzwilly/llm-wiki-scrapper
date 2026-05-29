## 1. Bridge Server — Core

- [x] 1.1 Bridge server accepts ingest requests: implement the Python HTTP server (python for bridge server) on `localhost:7842` — chosen over native messaging for simplicity and debuggability. `POST /ingest` returns 200 for valid payloads and 400 for missing required fields (`title`, `url`, `content`). Verify with `curl -X POST localhost:7842/ingest -H 'Content-Type: application/json' -d '{"title":"T","url":"U","content":"C"}'`.
- [x] 1.2 Duplicate URL detection (duplicate detection by URL): scanning `~/LLMwiki/sources/` for matching `url:` frontmatter returns 409 without writing a new file. Verify by posting the same URL twice and confirming only one sources file exists.
- [x] 1.3 Sources file written to vault (sources file as the handoff unit): bridge writes the file first so content is preserved even if Claude fails. File created at `~/LLMwiki/sources/<Title>.md` with YAML frontmatter (`title`, `url`, `saved`, `type`, `personal-note`, `highlights as frontmatter yaml`) and article body truncated to 50,000 chars. Verify file exists and frontmatter parses correctly after a valid POST.
- [x] 1.4 Claude CLI triggered as background process (non-blocking Claude trigger): after sources file is written, `claude` is spawned as a background process (bridge over native messaging approach — HTTP response sent before Claude completes). Verify the 200 response arrives before the Claude process exits (timing check via logs).
- [x] 1.5 Activity logged to file: each ingestion appends a timestamped line to `~/LLMwiki/bridge.log` with title, URL, and outcome. Verify log file grows by one line per request.

## 2. Bridge Server — Notification & Safety

- [x] 2.1 macOS notification sent on completion: after Claude subprocess exits with code 0, `osascript` fires a notification titled "LLMwiki" with concept count in body. Verify notification appears manually after a test ingestion.
- [x] 2.2 Claude not found on PATH fails fast: if `claude` is not on PATH at startup, the server logs a clear error and exits instead of starting silently broken. Verify by temporarily renaming `claude` and running the server.

## 3. launchd Service

- [x] 3.1 launchd plist auto-starts bridge server at login: `com.llmwiki.bridge.plist` loaded via `launchctl load` starts the bridge server and keeps it running. Verify with `curl localhost:7842/ingest` after loading the plist.
- [x] 3.2 Server restarts after crash: launchd plist has `KeepAlive: true`. Verify by killing the server process and confirming it restarts within a few seconds.
- [x] 3.3 Setup script installs the service: `bridge/install.sh` copies the plist to `~/Library/LaunchAgents/`, loads it, and prints a confirmation. Verify by running the script on a clean machine and checking the server responds on port 7842.

## 4. Chrome Extension — Content Script

- [x] 4.1 Content script captures text selections: selecting ≥10 chars on any page shows a floating "Add to Highlights" tooltip above the selection; <10 chars shows nothing. Verify manually on an article page.
- [x] 4.2 Highlights stored per URL: clicking "Add to Highlights" appends the text to `chrome.storage.local["highlights_<url>"]`. Verify via Chrome DevTools → Application → Storage after adding a highlight.
- [x] 4.3 Tooltip dismisses on click outside: clicking anywhere outside the tooltip hides it without storing the selection. Verify manually.
- [x] 4.4 Highlights survive popup close: highlights in storage persist after closing and reopening the popup on the same tab. Verify by adding a highlight, closing the popup, reopening it, and confirming the highlight appears.

## 5. Chrome Extension — Background Script

- [x] 5.1 Extension icon badge shows highlight count: the badge updates to show the number of stored highlights for the active tab; badge is cleared after a successful save. Verify by adding 2 highlights and confirming badge shows "2", then saving and confirming badge clears.

## 6. Chrome Extension — Popup UI

- [x] 6.1 Popup auto-fills article metadata: on open, the title field contains the active tab's page title (editable) and the URL is shown in muted text (read-only). Verify on any article page.
- [x] 6.2 Popup renders highlights with removal: stored highlights for the current URL are listed with × remove buttons; removing one updates storage and decreases badge count. Verify by removing a highlight and checking `chrome.storage.local`.
- [x] 6.3 Empty highlights state: when no highlights are stored, "Select text on the page to highlight" hint is shown. Verify on a tab with no highlights.
- [x] 6.4 Popup saves article to bridge server: clicking Save POSTs `{title, url, content, highlights, note}` to `localhost:7842/ingest`, transitions to "Saving…" spinner, then shows success or error state based on response. Verify full save flow end-to-end with bridge server running.
- [x] 6.5 Already saved state: a 409 response from the bridge shows "Already saved" in the popup. Verify by saving the same article twice.
- [x] 6.6 Bridge server not running state: a network error or unexpected status shows "Bridge server not running". Verify by stopping the bridge server and attempting a save.

## 7. llmwiki-ingest Skill Update

- [x] 7.1 Accept source file argument: invoking the skill with `--source-file ~/LLMwiki/sources/Article.md` reads from the local file and skips WebFetch. Verify by running the skill with a local sources file and confirming no network request is made.
- [x] 7.2 Highlights used as extraction signal: when the sources file frontmatter contains a `highlights` list, concepts linked to those passages are extracted and given richer "When to apply" sections. Verify by comparing extraction output with and without highlights on the same article.
- [x] 7.3 No highlights falls back to full judgment: when `highlights` is empty or absent, extraction behavior is unchanged from before. Verify on a sources file with no highlights field.

## 8. Integration & Validation

- [x] 8.1 End-to-end flow works: selecting text → clicking extension → adding note → clicking Save results in a new sources file in `~/LLMwiki/sources/`, new wiki entries in `~/LLMwiki/`, updated `LLMwiki Index.md`, and a macOS notification. Verify manually with a real article.
- [x] 8.2 Extension loads as unpacked: the extension loads in Chrome via `chrome://extensions` → Load unpacked without errors. Verify by checking the extensions page for any error indicators.
