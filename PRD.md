# PRD: LLMwiki Chrome Extension

## Problem Statement

Building a personal knowledge base requires capturing insights from articles read online. Today, the user must copy a URL, open a terminal, and manually invoke a CLI skill to ingest content into their LLMwiki vault. This multi-step context switch creates enough friction to break the reading-to-knowledge flow — making consistent capture unlikely over time.

---

## Solution

A personal Chrome extension that captures article content from any web page with a single click. The user optionally highlights passages and adds a personal note, then clicks Save. A local bridge server receives the content, writes it to the LLMwiki `sources/` folder, and automatically triggers Claude to extract concepts and update the wiki — all without opening a terminal. A macOS notification confirms completion.

---

## User Stories

### Content Capture
1. As a reader, I want to click the extension icon on any article page so that I can save it to my LLMwiki without leaving the browser.
2. As a reader, I want the article title and URL to be auto-filled in the extension popup so that I don't have to type them manually.
3. As a reader, I want to add a personal note explaining why I found the article interesting so that Claude can use my context during extraction.
4. As a reader, I want the personal note field to be optional so that I can save quickly when I don't have a specific reason to add.
5. As a reader, I want to select text on the page and have it saved as a highlight so that I can signal which passages mattered most to me.
6. As a reader, I want highlighting to be completely optional so that my reading flow is never interrupted.
7. As a reader, I want to see my highlights listed in the popup before saving so that I can review what I've marked.
8. As a reader, I want to remove a highlight from the popup before saving so that I can keep only the most relevant passages.
9. As a reader, I want highlights to persist on the page across popup opens/closes so that I don't lose them if I close the popup accidentally.
10. As a reader, I want the extension icon to show a badge when highlights exist on the current page so that I know I have unsaved highlights.

### Save & Feedback
11. As a reader, I want to click a single Save button to trigger the full ingestion pipeline so that no further action is required.
12. As a reader, I want the popup to show a "Saving..." status after I click Save so that I know the request was received.
13. As a reader, I want a macOS system notification when ingestion completes so that I know the wiki has been updated without checking Obsidian.
14. As a reader, I want the notification to tell me how many concepts were added or enriched so that I understand what was captured.
15. As a reader, I want the popup to show an error message if the bridge server is not running so that I know why the save failed.
16. As a reader, I want highlights and personal notes to be cleared after a successful save so that the extension is ready for the next article.

### Sources File
17. As a user, I want each saved article to create a single markdown file in `~/LLMwiki/sources/` so that raw content is preserved permanently.
18. As a user, I want the sources file to include the original URL so that I can always trace back to the original.
19. As a user, I want highlights to be stored in the sources file frontmatter so that Claude can read them as extraction signal.
20. As a user, I want the personal note to be stored in the sources file frontmatter so that it travels with the raw content.
21. As a user, I want the full article text to be stored in the sources file body so that ingestion works even if the original URL goes dead.
22. As a user, I want duplicate URLs to be detected so that saving the same article twice doesn't create duplicate sources files.

### Wiki Ingestion
23. As a user, I want Claude to automatically run the llmwiki-ingest skill after the sources file is saved so that wiki entries are created without opening a terminal.
24. As a user, I want Claude to use my highlights as extraction signal so that concepts linked to highlighted passages are prioritized.
25. As a user, I want Claude to enrich existing wiki entries rather than create duplicates so that the wiki stays clean over time.
26. As a user, I want the LLMwiki Index to be updated automatically after ingestion so that new entries are always reflected.

### Bridge Server
27. As a user, I want the bridge server to start automatically at Mac login so that it's always available without manual setup.
28. As a user, I want the bridge server to run silently in the background so that it never interrupts my work.
29. As a user, I want the bridge server to log ingestion activity to a file so that I can debug issues if something goes wrong.

---

## Implementation Decisions

### Module breakdown

| Module | Responsibility |
|---|---|
| Content Extractor | Reads article title, URL, and full body text from the active tab's DOM |
| Highlight Manager | Listens for text selections in content script, stores highlighted passages keyed by URL in extension local storage |
| Extension Popup | UI — auto-fills title/URL, renders highlights list, personal note input, Save button, status display |
| Bridge Client | POSTs the assembled payload (title, url, content, highlights, note) to localhost bridge server |
| Bridge Server | HTTP server on localhost:7842; receives POST, orchestrates sources write + Claude trigger + notification |
| Sources File Writer | Formats and writes the markdown sources file to `~/LLMwiki/sources/[Title].md` |
| Claude CLI Trigger | Shells out to `claude` CLI, invoking llmwiki-ingest with the sources file path |
| Notification Service | Sends macOS system notification via `osascript` after ingestion completes |
| launchd Plist | Keeps bridge server running as a background macOS service, auto-starts at login |

### Key decisions
- Bridge server runs on `localhost:7842`. Extension sends a single POST with all payload data.
- Sources file is written before Claude is triggered. If Claude fails, raw content is still preserved.
- Claude is triggered non-blocking — bridge server responds to the extension immediately after writing the sources file, then triggers Claude in the background. This keeps the popup responsive.
- Duplicate detection: before writing, bridge server checks if a sources file with matching URL already exists in frontmatter.
- Highlights stored in sources file frontmatter as a YAML list under `highlights:`.
- The llmwiki-ingest skill is updated to accept a `--source-file` argument so it reads from a local file instead of fetching a URL.
- macOS notification sent by bridge server after Claude completes, carrying concept count from Claude's output.
- Bridge server is Python (simpler dependency story for a non-developer user).

---

## Testing Decisions

Good tests verify external behavior — what the module produces, not how it produces it.

| Module | What to test |
|---|---|
| Content Extractor | Given a sample HTML page, returns correct title, URL, and body text |
| Sources File Writer | Given a payload, produces correctly formatted markdown with valid frontmatter |
| Duplicate Detection | Given an existing sources file with matching URL, returns duplicate signal without writing |
| Bridge Server API | POST with valid payload returns 200; POST with missing fields returns 400 |
| Highlight Manager | Highlights persist across popup open/close; cleared after successful save |
| Claude CLI Trigger | Correct command string is constructed from sources file path |

No tests needed for: launchd plist (infrastructure), macOS notification (OS API), popup UI rendering (visual).

---

## Out of Scope

- YouTube video transcript extraction
- PDF content extraction
- Safari / Firefox support
- Multi-vault support
- Cloud sync or remote bridge
- Sharing or collaboration features
- Editing or deleting existing sources files from the extension

---

## Further Notes

- The llmwiki-ingest skill already exists at `~/.claude/skills/llmwiki-ingest/` and handles deduplication, enrichment, and index updates. The extension does not need to replicate this logic.
- The vault's `CLAUDE.md` already documents governance rules. The skill reads it automatically.
- The Chrome extension does not need to be published to the Chrome Web Store — it can be loaded as an unpacked extension for personal use.
- Future versions may support YouTube (via transcript API) and PDFs (via embedded viewer content script). Explicitly deferred from v1.
