## Why

Users watch YouTube videos as a primary source of learning but have no way to ingest them into LLMwiki — the extension only handles articles and PDFs. YouTube transcripts contain the same extractable knowledge as written articles, and the bridge server already has a pattern (PDF extraction) that maps cleanly onto transcript fetching.

## What Changes

- Chrome extension popup detects `youtube.com/watch` URLs, hides highlights, shows a YouTube badge, and sends `type: "youtube"` payloads with no content field
- Bridge server gains `extract_youtube_transcript(url)` which fetches and joins the transcript as plain text via `youtube-transcript-api`, raising on unavailability
- Bridge server `do_POST` handler gains a `type: "youtube"` branch (mirrors `type: "pdf"`) that calls transcript extraction, returns 502 on failure, writes sources file with `type: youtube`, and spawns Claude
- `requirements.txt` adds `youtube-transcript-api`

## Non-Goals

- Audio transcription via Whisper for videos without captions — if no transcript is available, the error state is surfaced
- Including the video description alongside the transcript
- Language/locale selection for multi-language transcripts
- Timestamp-based concept anchoring
- YouTube Shorts, playlists, or channel pages

## Capabilities

### New Capabilities

- `youtube-ingestion`: Transcript-based ingestion of YouTube videos through the extension popup and bridge server, producing sources files with `type: youtube` for Claude concept extraction

### Modified Capabilities

(none)

## Impact

- Affected code: `extension/popup.js`, `extension/popup.html`, `bridge/server.py`, `bridge/requirements.txt`
- New dependency: `youtube-transcript-api` (PyPI, no API key required)
