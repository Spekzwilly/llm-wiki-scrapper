## 1. Bridge: Dependency and PDF Extraction

- [x] 1.1 Add `pymupdf` to a new `bridge/requirements.txt` file and document the install command, so the dependency is explicit for anyone setting up the bridge environment. Verified by: file exists and `pip install -r bridge/requirements.txt` succeeds without error.

- [x] 1.2 Implement server-side extraction with pymupdf — add `extract_pdf_text(url: str) -> str` to `bridge/server.py` that downloads PDF bytes via `urllib.request` and returns concatenated page text via `fitz.open(stream=..., filetype="pdf")`. This satisfies the **PDF save via server-side extraction** requirement. Verified by: calling the function with a real arXiv PDF URL returns a non-empty string.

## 2. Bridge: POST /ingest Protocol Update

- [x] 2.1 Update `do_POST` in `bridge/server.py` to branch on the **explicit type field in POST protocol**: when `type == "pdf"`, require only `title` and `url` (skip the `content` required-field check), call `extract_pdf_text(url)`, and return HTTP 502 with `{"error": "pdf extraction failed"}` if it raises. Verified by: POSTing `{title, url, type: "pdf"}` without `content` returns 200 and creates a sources file.

- [x] 2.2 Update `write_sources_file` in `bridge/server.py` to accept a `source_type` parameter (default `"article"`) and write it as the `type:` frontmatter field, satisfying the **PDF sources file format** requirement. Verified by: sources file created from a PDF POST contains `type: pdf` in YAML frontmatter.

- [x] 2.3 Confirm **duplicate PDF detection** continues to work unchanged — `find_existing_url` checks `url:` in frontmatter regardless of `type`. Verified by: POSTing the same PDF URL twice returns HTTP 409 on the second request.

## 3. Extension: PDF Tab Detection and UI Adaptation

- [x] 3.1 Add `isPdfUrl(url)` helper to `extension/popup.js` that returns `true` when the URL matches `/\.pdf(\?|$)/i`, implementing **PDF detection via URL heuristic** and the **PDF tab detection** requirement. Verified by: unit check — `isPdfUrl("https://arxiv.org/pdf/2301.12345")` returns `true`, `isPdfUrl("https://example.com/article")` returns `false`.

- [x] 3.2 Add `id="highlights-section"` to the highlights `<div class="section">` wrapper in `extension/popup.html` and add a hidden `<span id="pdf-badge">PDF</span>` near the `#url-display` element. Verified by: elements exist in DOM and are referenceable from JS.

- [x] 3.3 In `init()` in `extension/popup.js`, call `isPdfUrl(currentUrl)` and, if true, hide `#highlights-section` and show `#pdf-badge` — satisfying **highlights hidden for PDF tabs** in the design. Verified by: loading the popup on a `.pdf` tab shows the PDF badge and no highlights section.

## 4. Extension: Save Flow Update

- [x] 4.1 Update `save()` in `extension/popup.js` so that when on a PDF tab, it skips `getPageContent()`, sets `content` to empty, and adds `type: "pdf"` to the POST body — implementing the **PDF save via server-side extraction** protocol. Also suppress the `view-no-content` error state for PDF tabs (empty content is expected). Verified by: clicking Save on a PDF tab sends `{title, url, note, type: "pdf"}` to the bridge and transitions to the processing view.

## 5. End-to-End Verification

- [x] 5.1 Manual smoke test — article path: save a regular article URL and confirm the popup, badge, sources file, and concept extraction all behave identically to before this change. Verified by: no regressions in article ingestion flow.

- [x] 5.2 Manual smoke test — **concept extraction for PDFs**: open an arXiv PDF in Chrome, click Save, add a note, confirm the processing view appears, wait for the macOS notification, and verify the sources file at `~/LLMwiki/sources/` contains `type: pdf` frontmatter and extracted text. Verified by: popup shows concept count matching the macOS notification.

- [x] 5.3 Manual smoke test — slide deck PDF: repeat 5.2 with a slide deck PDF to confirm `pymupdf` **server-side extraction with pymupdf** handles non-plain-text layouts and produces non-empty text. Verified by: sources file body is non-empty.
