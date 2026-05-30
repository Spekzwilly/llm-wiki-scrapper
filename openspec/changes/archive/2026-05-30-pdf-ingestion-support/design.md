## Context

The LLMwiki extension saves web articles to `~/LLMwiki/` via a two-part system: a Chrome extension that extracts page text using `document.body.innerText`, and a Python bridge server (`localhost:7842`) that writes the sources file and triggers Claude concept extraction. Chrome's built-in PDF viewer is sandboxed — content scripts cannot run in it — so the current text extraction path produces nothing for PDF tabs.

## Goals / Non-Goals

**Goals:**

- One-click save for web-hosted PDFs (URLs) using the same popup flow as articles
- Server-side text extraction that handles complex layouts (slide decks, multi-column papers)
- Adapt the popup UI for PDF tabs (hide non-functional highlights section)
- Keep the article save path entirely unchanged

**Non-Goals:**

- Local filesystem PDFs (`file://` URLs)
- Text selection / highlights within Chrome's PDF viewer (sandbox prevents it)
- OCR for scanned / image-only PDFs
- Supporting other binary formats (DOCX, EPUB)
- Tuning Claude concept extraction specifically for PDFs

## Decisions

### PDF Detection via URL Heuristic

The popup checks `tab.url` against `/\.pdf(\?|$)/i` to identify PDF tabs. Content-type sniffing via a HEAD request would be more accurate but adds latency and a network call before the user even clicks Save. URL matching covers all practical cases (arXiv, Google Slides exports, documentation sites).

Alternative considered: try `getPageContent()` and treat empty result as PDF indicator. Rejected — empty results also occur on SPAs and loading pages, making the signal unreliable.

### Server-Side Extraction with pymupdf

The bridge downloads the PDF bytes via `urllib.request` (stdlib, no new dep) and extracts text with `pymupdf` (`fitz`). `pymupdf` is chosen over `pypdf` because it handles complex layouts (multi-column, slide decks, mixed graphics) and is significantly faster. `pdfminer.six` was considered but has a more complex API with no quality advantage for this use case.

### Explicit Type Field in POST Protocol

When saving a PDF, the extension sends `"type": "pdf"` in the POST body and omits `content`. The bridge branches on this field: skips the content required-field check and performs download + extraction instead. An explicit field is cleaner than inferring intent from an empty content string, and makes the protocol self-documenting.

### Highlights Hidden for PDF Tabs

Content scripts do not run in Chrome's PDF viewer, so no highlights can be captured for PDFs. Rather than showing an empty, non-functional highlights section, the popup hides it entirely when a PDF tab is detected. The `view-no-content` error state is also suppressed for PDF tabs since extraction is handled server-side.

## Implementation Contract

**PDF detection**
The popup SHALL identify a tab as a PDF when `tab.url` matches `/\.pdf(\?|$)/i`. This check occurs in `init()` before rendering the form.

**Popup UI adaptation**
When on a PDF tab, the highlights section SHALL be hidden and a PDF indicator label SHALL be visible near the URL display. The title and personal note fields SHALL remain active.

**POST body shape (PDF)**
```json
{ "title": "…", "url": "https://…/paper.pdf", "note": "…", "type": "pdf" }
```
The `content` field SHALL be omitted. The `highlights` field SHALL be omitted or empty.

**Bridge extraction**
On receiving `type: "pdf"`, the bridge SHALL download the PDF from `url` and extract text using `pymupdf`. If download or extraction fails (network error, malformed PDF, timeout), the bridge SHALL return HTTP 502 and the popup SHALL display the existing error view.

**Sources frontmatter**
PDF-sourced files SHALL use `type: pdf` in YAML frontmatter. All other fields (title, url, saved, personal-note, highlights) remain structurally identical.

**Acceptance criteria**
1. Opening a `.pdf` URL → popup shows PDF indicator, highlights section hidden
2. Clicking Save on a PDF → sources file created with `type: pdf` and non-empty body
3. macOS notification fires after Claude finishes processing
4. Saving the same PDF URL twice → 409 response, duplicate view shown
5. Saving a regular article URL → behavior unchanged

## Risks / Trade-offs

- [PDFs without `.pdf` in URL] → Not detected as PDF; `getPageContent()` returns empty; user sees `view-no-content` error. Mitigation: acceptable edge case for v1; a manual "Force PDF mode" button can be added later.
- [Large PDFs] → Download may be slow or time out (urllib default is 30s in the plan). Mitigation: set explicit timeout; the 50k character truncation in `write_sources_file` caps processing cost downstream.
- [pymupdf install size] → pymupdf has a C extension (~20 MB). Mitigation: documented in `requirements.txt`; users already manage a Python environment for the bridge.
- [Scanned PDFs] → pymupdf returns empty text per page for image-only pages. Mitigation: the sources file is still created with whatever text was extractable; Claude will produce fewer concepts but won't error.
