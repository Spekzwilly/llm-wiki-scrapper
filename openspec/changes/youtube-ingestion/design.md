## Context

The LLMwiki system ingests knowledge sources (articles, PDFs) via a Chrome extension + Python bridge server. The bridge server already handles source-type branching: articles are provided with full content in the request payload, PDFs have their content extracted server-side. YouTube videos require a third branch: the extension sends only the URL (no content), and the bridge fetches the transcript server-side using `youtube-transcript-api`.

The existing PDF flow is the direct template. The popup detects a PDF URL → shows a badge → sends `type: "pdf"` with no content → bridge calls `extract_pdf_text(url)` → writes sources file → spawns Claude. YouTube follows the same shape, replacing pymupdf with `youtube-transcript-api`.

## Goals / Non-Goals

**Goals:**

- Detect YouTube video URLs in the popup and adapt the UI (badge, no highlights)
- Extract plain-text transcripts on the bridge server with no user-facing configuration
- Surface a clear error when no transcript is available
- Produce sources files tagged `type: youtube` for vault querying

**Non-Goals:**

- Whisper/audio fallback for captionless videos
- Video description ingestion
- Language selection for multi-language transcripts
- Timestamp-based concept anchoring
- YouTube Shorts, playlists, or channel page support

## Decisions

### YouTube URL detection uses a URL pattern match, not the YouTube Data API

A regex check on `youtube.com/watch` (matching the `isPdfUrl` pattern) requires no credentials and works offline. The Data API would add OAuth complexity with no benefit for this use case.

### Transcript extraction happens on the bridge server, not in the extension

The extension already sends no content for PDFs — the server fetches it. Keeping extraction server-side means no changes to the extension's content script, no new browser permissions, and a single extraction code path (Python) that is testable in isolation.

### `youtube-transcript-api` over `yt-dlp` or the YouTube Data API

`youtube-transcript-api` is a single pip dependency with no API key, no binary, and a simple `YouTubeTranscriptApi.get_transcript(video_id)` interface. `yt-dlp` is a large binary better suited to audio/video download. The Data API requires OAuth. For transcript-only extraction, `youtube-transcript-api` is the minimal-surface option.

### Timestamps are stripped; plain text is joined

Timestamps are noise for concept extraction. `youtube-transcript-api` returns a list of `{"text": ..., "start": ..., "duration": ...}` dicts. Joining `chunk["text"]` with spaces produces clean prose that Claude processes the same as article body text.

### Error on missing transcript; no fallback

Returning a `502` with a human-readable message ("No transcript available for this video") is consistent with the PDF extraction failure path. A Whisper fallback would require audio download infrastructure out of scope for this change.

## Implementation Contract

### Extension popup behavior

- `isYoutubeUrl(url)` returns `true` for URLs matching `youtube.com/watch`
- When `currentIsYoutube` is `true`: `#highlights-section` is hidden, `#youtube-badge` is visible
- `save()` sends `{ title, url, note, type: "youtube" }` — no `content`, no `highlights`
- All other popup views (saving, processing, success, duplicate, error) behave identically to article/PDF flows

### Bridge server behavior

- `extract_youtube_transcript(url: str) -> str`: parses video ID from URL, calls `YouTubeTranscriptApi.get_transcript(video_id)`, joins all chunk `text` values with a space separator, returns the string
- If `get_transcript` raises (no captions, private video, network error): the exception propagates; `do_POST` returns `{"error": "No transcript available for this video"}` with HTTP 502
- `do_POST` with `type: "youtube"`: validates `title` and `url` present, runs duplicate detection, calls `extract_youtube_transcript`, writes sources file with `source_type="youtube"`, returns 200, spawns Claude thread
- Sources file frontmatter: `type: youtube`

### Acceptance criteria

- Opening popup on `youtube.com/watch?v=...`: YouTube badge visible, highlights section hidden
- Saving a video with a transcript: sources file written at `~/LLMwiki/sources/<Title>.md` with `type: youtube`, Claude spawned, macOS notification fires on completion
- Saving a video with no transcript: popup shows error view with message from bridge
- Saving a video already in vault: popup shows duplicate view (409)
- `bridge/test_youtube.py`: `extract_youtube_transcript` called with a known public video ID returns a non-empty string

## Risks / Trade-offs

- [Risk] `youtube-transcript-api` depends on YouTube's internal transcript endpoint, which could break on YouTube API changes → Mitigation: the library is actively maintained; failures surface as 502 errors, not silent data loss
- [Risk] Auto-generated captions on technical content can be low quality (no punctuation, wrong terminology) → Mitigation: accepted trade-off; manually uploaded transcripts are preferred by the library when available
- [Risk] Very long videos produce very large transcript strings → Mitigation: the 50,000-character truncation already applied in `write_sources_file` caps the sources file size
