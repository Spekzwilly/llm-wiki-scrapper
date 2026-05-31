## 1. Bridge Server — Dependency and Transcript Extraction

- [x] 1.1 Add `youtube-transcript-api` to `bridge/requirements.txt` — the decision "`youtube-transcript-api` over `yt-dlp` or the YouTube Data API" is implemented here; verify by running `pip install -r bridge/requirements.txt` without error
- [x] 1.2 Implement `extract_youtube_transcript(url: str) -> str` satisfying the requirement "Transcript extraction on bridge server": parse video ID from URL, call `YouTubeTranscriptApi.get_transcript(video_id)`, join chunk `text` values with spaces (decision: "Timestamps are stripped; plain text is joined"), return the plain string — verify with `bridge/test_youtube.py` calling the function against a known public video ID and asserting a non-empty string is returned
- [x] 1.3 Verify the error path from the decision "Error on missing transcript; no fallback": when `get_transcript` raises, the exception propagates out of `extract_youtube_transcript` — verify in `bridge/test_youtube.py` that calling the function with a captionless video ID raises an exception

## 2. Bridge Server — YouTube Ingestion Branch

- [x] 2.1 Add a `type == "youtube"` branch in `do_POST` implementing the contract "Bridge server behavior": validate `title` and `url` are present, run `find_existing_url`, call `extract_youtube_transcript` (decision: "Transcript extraction happens on the bridge server, not in the extension"), write sources file with `source_type="youtube"` (requirement "Sources file written with type youtube"), return HTTP 200, spawn Claude satisfying the requirement "Claude spawned after YouTube sources file written" — verify by sending `POST /ingest` with `type: "youtube"` and asserting a sources file is written with `type: youtube` in frontmatter
- [x] 2.2 Confirm the no-transcript error surface from the decision "Error on missing transcript; no fallback": when `extract_youtube_transcript` raises, `do_POST` returns HTTP 502 with `{"error": "No transcript available for this video"}` — verify by sending a request with a captionless video URL and asserting the 502 response body and absence of a new sources file
- [x] 2.3 Confirm requirement "Duplicate detection applies to YouTube videos": sending the same YouTube URL twice returns HTTP 409 on the second request — verify manually or via test

## 3. Chrome Extension — YouTube URL Detection

- [x] 3.1 Add `isYoutubeUrl(url)` predicate satisfying requirement "YouTube URL detection in popup": returns `true` for URLs matching `youtube.com/watch`, `false` otherwise (decision: "YouTube URL detection uses a URL pattern match, not the YouTube Data API") — verify by inspecting the function's return value on a YouTube URL and a non-YouTube URL in the extension popup context
- [x] 3.2 Set `currentIsYoutube` flag in `init()` using `isYoutubeUrl` (mirrors the `currentIsPdf` pattern; implements decision "Extension popup behavior") — verify by opening the popup on a YouTube video URL and confirming the flag is set

## 4. Chrome Extension — YouTube Badge and UI Adaptation

- [x] 4.1 Add `#youtube-badge` element to `extension/popup.html` URL line satisfying requirement "YouTube badge displayed for video pages": styled consistently with `#pdf-badge` (red pill, uppercase, starts hidden) — verify it is visible when `currentIsYoutube` is `true` and hidden otherwise
- [x] 4.2 In `init()`, when `currentIsYoutube` is `true`, hide `#highlights-section` (requirement "Highlights section hidden for YouTube videos") and reveal `#youtube-badge` — verify by opening popup on a YouTube video tab: highlights section absent, YouTube badge visible

## 5. Chrome Extension — YouTube Save Payload

- [x] 5.1 Add YouTube branch in `save()` satisfying requirement "YouTube payload sent on save" per decision "Extension popup behavior": send `{ title, url, note, type: "youtube" }` with no `content` or `highlights` — verify by clicking Save on a YouTube popup and confirming the bridge log shows the correct payload

## 6. End-to-End Verification (Acceptance Criteria)

- [x] 6.1 Full save flow (acceptance criteria): open popup on a YouTube video with a transcript, click Save, confirm popup transitions saving → processing → success, sources file written with `type: youtube`, concepts extracted, macOS notification fires
- [x] 6.2 Error flow (acceptance criteria): open popup on a YouTube video with no available transcript, click Save, confirm popup shows error view with a meaningful message from the bridge
