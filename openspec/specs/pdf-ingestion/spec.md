# pdf-ingestion Specification

## Purpose

TBD - created by archiving change 'pdf-ingestion-support'. Update Purpose after archive.

## Requirements

### Requirement: PDF tab detection

The extension popup SHALL detect when the active tab is displaying a web-hosted PDF by matching the tab URL against the pattern `/\.pdf(\?|$)/i`.

#### Scenario: PDF URL detected

- **WHEN** the active tab URL ends with `.pdf` or contains `.pdf?`
- **THEN** the popup SHALL enter PDF mode: hide the highlights section and show a PDF indicator label

#### Scenario: Non-PDF URL not affected

- **WHEN** the active tab URL does not match the PDF pattern
- **THEN** the popup SHALL display the standard article form with highlights section visible

##### Example: URL classification

| URL | PDF mode? |
|-----|-----------|
| `https://arxiv.org/pdf/2301.12345` | Yes |
| `https://example.com/paper.pdf?v=2` | Yes |
| `https://example.com/article` | No |
| `https://example.com/pdf-viewer` | No |


<!-- @trace
source: pdf-ingestion-support
updated: 2026-05-30
code:
  - extension/icons/icon32.png
  - extension/popup.js
  - prototype.html
  - extension/icons/icon48.png
  - logo-preview.html
  - bridge/requirements.txt
  - extension/icons/icon16.png
  - extension/icons/icon128.png
  - extension/icons/icon.svg
  - bridge/server.py
  - extension/manifest.json
  - extension/popup.html
  - extension/background.js
-->

---
### Requirement: PDF save via server-side extraction

When saving a PDF tab, the extension SHALL send `{ title, url, note, type: "pdf" }` to the bridge — omitting the `content` field — and the bridge SHALL download the PDF from the URL and extract its text using `pymupdf`.

#### Scenario: Successful PDF save

- **WHEN** the user clicks Save on a PDF tab
- **THEN** the extension SHALL POST `{ title, url, note, type: "pdf" }` to `POST /ingest`
- **THEN** the bridge SHALL respond with HTTP 200 after writing the sources file
- **THEN** the popup SHALL show the processing view and begin polling `/status`

#### Scenario: PDF download failure

- **WHEN** the bridge cannot download or parse the PDF (network error, malformed file, timeout)
- **THEN** the bridge SHALL return HTTP 502
- **THEN** the popup SHALL display the error view


<!-- @trace
source: pdf-ingestion-support
updated: 2026-05-30
code:
  - extension/icons/icon32.png
  - extension/popup.js
  - prototype.html
  - extension/icons/icon48.png
  - logo-preview.html
  - bridge/requirements.txt
  - extension/icons/icon16.png
  - extension/icons/icon128.png
  - extension/icons/icon.svg
  - bridge/server.py
  - extension/manifest.json
  - extension/popup.html
  - extension/background.js
-->

---
### Requirement: PDF sources file format

The bridge SHALL write PDF-sourced entries to `~/LLMwiki/sources/<Title>.md` with `type: pdf` in YAML frontmatter. All other frontmatter fields (title, url, saved, personal-note, highlights) SHALL be structurally identical to article sources files.

#### Scenario: Sources file created for PDF

- **WHEN** the bridge successfully extracts text from a PDF
- **THEN** the sources file MUST contain `type: pdf` in frontmatter
- **THEN** the sources file body MUST contain the extracted text (up to 50,000 characters)

#### Scenario: Highlights field for PDFs

- **WHEN** a sources file is created from a PDF
- **THEN** the `highlights` frontmatter field SHALL be an empty array


<!-- @trace
source: pdf-ingestion-support
updated: 2026-05-30
code:
  - extension/icons/icon32.png
  - extension/popup.js
  - prototype.html
  - extension/icons/icon48.png
  - logo-preview.html
  - bridge/requirements.txt
  - extension/icons/icon16.png
  - extension/icons/icon128.png
  - extension/icons/icon.svg
  - bridge/server.py
  - extension/manifest.json
  - extension/popup.html
  - extension/background.js
-->

---
### Requirement: Duplicate PDF detection

The bridge SHALL reject a PDF save request if the URL already exists in any sources file frontmatter, returning HTTP 409.

#### Scenario: Duplicate PDF URL blocked

- **WHEN** the user attempts to save a PDF whose URL is already present in `~/LLMwiki/sources/`
- **THEN** the bridge SHALL return HTTP 409
- **THEN** the popup SHALL display the duplicate view


<!-- @trace
source: pdf-ingestion-support
updated: 2026-05-30
code:
  - extension/icons/icon32.png
  - extension/popup.js
  - prototype.html
  - extension/icons/icon48.png
  - logo-preview.html
  - bridge/requirements.txt
  - extension/icons/icon16.png
  - extension/icons/icon128.png
  - extension/icons/icon.svg
  - bridge/server.py
  - extension/manifest.json
  - extension/popup.html
  - extension/background.js
-->

---
### Requirement: Concept extraction for PDFs

After writing the PDF sources file, the bridge SHALL trigger the same Claude `/llmwiki-ingest` pipeline used for articles. On completion, a macOS notification SHALL fire and the popup SHALL display the concept count.

#### Scenario: Concepts extracted from PDF

- **WHEN** Claude finishes processing a PDF sources file
- **THEN** `/status` SHALL return `{ state: "done", concepts: [...] }`
- **THEN** the popup SHALL show the success view with extracted concept names
- **THEN** a macOS notification SHALL display the concept count

<!-- @trace
source: pdf-ingestion-support
updated: 2026-05-30
code:
  - extension/icons/icon32.png
  - extension/popup.js
  - prototype.html
  - extension/icons/icon48.png
  - logo-preview.html
  - bridge/requirements.txt
  - extension/icons/icon16.png
  - extension/icons/icon128.png
  - extension/icons/icon.svg
  - bridge/server.py
  - extension/manifest.json
  - extension/popup.html
  - extension/background.js
-->