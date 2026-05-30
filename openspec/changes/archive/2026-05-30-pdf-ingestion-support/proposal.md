## Why

Chrome's built-in PDF viewer is sandboxed — content scripts cannot inject into it, so the extension's `document.body.innerText` approach yields nothing for PDFs. Users who read web-hosted papers and slide decks (arXiv, Google Slides exports) have no way to save them to LLMwiki without manual copy-paste.

## What Changes

- The extension popup detects PDF tabs via URL heuristic and adapts its UI (hides highlights, shows PDF indicator)
- On save, the extension sends `type: "pdf"` in the POST body with no content field, signaling the bridge to handle extraction
- The bridge server downloads the PDF from the URL and extracts text server-side using `pymupdf`
- Sources files created from PDFs use `type: pdf` frontmatter instead of `type: article`
- A `requirements.txt` is added to the bridge directory to document the `pymupdf` dependency

## Capabilities

### New Capabilities

- `pdf-ingestion`: Detect PDF tabs, extract text server-side from a URL, and save to the vault with the same one-click flow as articles

### Modified Capabilities

(none)

## Impact

- Affected code: `extension/popup.js`, `extension/popup.html`, `bridge/server.py`
- New file: `bridge/requirements.txt`
- New dependency: `pymupdf` (pip)
