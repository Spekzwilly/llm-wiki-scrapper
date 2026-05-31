# youtube-ingestion Spec

## Overview

The `youtube-ingestion` capability enables saving YouTube videos into the LLMwiki vault via the Chrome extension. The extension detects YouTube video URLs, adapts the popup UI, and sends a transcript extraction request to the bridge server. The bridge server fetches the transcript, writes a sources file, and triggers Claude concept extraction — identical to the article and PDF flows.

---

## ADDED Requirements

### Requirement: YouTube URL detection in popup

The extension popup SHALL detect URLs matching `youtube.com/watch` and set a `currentIsYoutube` flag.

#### Scenario: YouTube video URL detected

- **WHEN** the popup opens on a tab whose URL contains `youtube.com/watch`
- **THEN** `currentIsYoutube` is set to `true`

#### Scenario: Non-YouTube URL not flagged

- **WHEN** the popup opens on a tab whose URL does not match `youtube.com/watch`
- **THEN** `currentIsYoutube` remains `false`

---

### Requirement: YouTube badge displayed for video pages

When a YouTube video is detected, the popup SHALL show a YouTube badge in the URL line.

#### Scenario: YouTube badge visible on video page

- **WHEN** `currentIsYoutube` is `true`
- **THEN** the `#youtube-badge` element is visible in the URL line

#### Scenario: YouTube badge hidden on non-video pages

- **WHEN** `currentIsYoutube` is `false`
- **THEN** the `#youtube-badge` element remains hidden

---

### Requirement: Highlights section hidden for YouTube videos

The popup SHALL hide the highlights section when on a YouTube video page, as text selection does not apply to video content.

#### Scenario: Highlights hidden on YouTube page

- **WHEN** `currentIsYoutube` is `true`
- **THEN** the `#highlights-section` element is hidden

---

### Requirement: YouTube payload sent on save

When saving a YouTube video, the popup SHALL send `{ title, url, note, type: "youtube" }` to the bridge server with no `content` or `highlights` fields.

#### Scenario: Save sends YouTube payload

- **WHEN** the user clicks Save on a YouTube video popup
- **THEN** the bridge receives a POST body with `type: "youtube"`, `title`, `url`, and `note`
- **AND** no `content` or `highlights` fields are included

---

### Requirement: Transcript extraction on bridge server

The bridge server SHALL extract a plain-text transcript for a YouTube video URL using `youtube-transcript-api`, stripping all timestamp metadata.

#### Scenario: Transcript extracted as plain text

- **WHEN** the bridge receives `type: "youtube"` with a valid video URL
- **THEN** `extract_youtube_transcript(url)` parses the video ID, fetches the transcript, and returns a single string of all text chunks joined by spaces

#### Scenario: No transcript available returns error

- **WHEN** `extract_youtube_transcript(url)` is called for a video with no available transcript
- **THEN** the function raises an exception
- **AND** the bridge returns HTTP 502 with `{"error": "No transcript available for this video"}`

---

### Requirement: Sources file written with type youtube

The bridge server SHALL write a sources file with `type: youtube` in the frontmatter for successfully extracted YouTube transcripts.

#### Scenario: Sources file created for YouTube video

- **WHEN** transcript extraction succeeds
- **THEN** a sources file is written at `~/LLMwiki/sources/<Title>.md`
- **AND** the frontmatter contains `type: youtube`
- **AND** the file body contains the plain-text transcript

---

### Requirement: Duplicate detection applies to YouTube videos

The bridge server SHALL reject YouTube video saves if the URL already exists in any sources file frontmatter, returning HTTP 409.

#### Scenario: Duplicate YouTube video rejected

- **WHEN** the bridge receives `type: "youtube"` for a URL already present in `~/LLMwiki/sources/`
- **THEN** the bridge returns HTTP 409
- **AND** no new sources file is written

---

### Requirement: Claude spawned after YouTube sources file written

After writing the sources file, the bridge SHALL spawn Claude via the `llmwiki-ingest` skill in a background thread, identical to the article and PDF flows.

#### Scenario: Claude processes YouTube transcript

- **WHEN** the sources file for a YouTube video is successfully written
- **THEN** Claude is spawned with `--dangerously-skip-permissions -p "/llmwiki-ingest --source-file <path>"` with `cwd=~/LLMwiki`
- **AND** a macOS notification fires on completion or error
