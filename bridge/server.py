#!/usr/bin/env python3
"""LLMwiki bridge server — receives article saves from Chrome extension."""

import http.server
import json
import logging
import re
import shutil
import subprocess
import threading
import urllib.request
from datetime import date, datetime
from pathlib import Path

import fitz  # pymupdf
from youtube_transcript_api import YouTubeTranscriptApi

VAULT = Path.home() / "LLMwiki"
SOURCES = VAULT / "sources"
LOG_FILE = VAULT / "bridge.log"
PORT = 7842

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# Ingestion status — read by GET /status
_status_lock = threading.Lock()
_status: dict = {"state": "idle", "title": "", "concepts": [], "error": ""}


def _set_status(**kwargs) -> None:
    with _status_lock:
        _status.update(kwargs)


def _get_status() -> dict:
    with _status_lock:
        return dict(_status)


def extract_pdf_text(url: str) -> str:
    """Download a PDF from url and return concatenated page text."""
    with urllib.request.urlopen(url, timeout=30) as resp:
        pdf_bytes = resp.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n\n".join(page.get_text() for page in doc)


def extract_youtube_transcript(url: str) -> str:
    """Fetch and join transcript text for a YouTube video URL, stripping timestamps."""
    match = re.search(r"[?&]v=([^&]+)", url)
    if not match:
        raise ValueError(f"Could not parse video ID from URL: {url}")
    video_id = match.group(1)
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    transcript = next(iter(transcript_list))
    fetched = transcript.fetch()
    return " ".join(snippet.text for snippet in fetched.snippets)


def to_safe_title(text: str) -> str:
    """Title Case with special characters removed."""
    cleaned = re.sub(r"[^\w\s-]", "", text)
    return " ".join(word.capitalize() for word in cleaned.split())


def find_existing_url(url: str) -> bool:
    """Return True if any sources file already has this url: in frontmatter."""
    if not SOURCES.exists():
        return False
    for f in SOURCES.glob("*.md"):
        try:
            if f"url: {url}" in f.read_text(encoding="utf-8"):
                return True
        except OSError:
            pass
    return False


def write_sources_file(title: str, url: str, content: str, note: str, highlights: list, source_type: str = "article") -> Path:
    """Write article/PDF to ~/LLMwiki/sources/<Title>.md with YAML frontmatter."""
    SOURCES.mkdir(parents=True, exist_ok=True)
    safe_title = to_safe_title(title)
    path = SOURCES / f"{safe_title}.md"

    if highlights:
        highlights_yaml = "highlights:\n" + "".join(f"  - {h}\n" for h in highlights)
    else:
        highlights_yaml = "highlights: []\n"

    frontmatter = (
        f"---\n"
        f"title: {title}\n"
        f"url: {url}\n"
        f"saved: {date.today().isoformat()}\n"
        f"type: {source_type}\n"
        f"personal-note: {note or ''}\n"
        f"{highlights_yaml}"
        f"---\n\n"
    )
    path.write_text(frontmatter + content[:50000], encoding="utf-8")
    return path


def append_log(title: str, url: str, outcome: str) -> None:
    """Append one timestamped line to bridge.log."""
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {outcome} | {title} | {url}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        log.error("Failed to write log: %s", e)


def trigger_claude(sources_path: Path, title: str, url: str) -> None:
    """Spawn claude as a background process; notify via osascript when done."""
    _set_status(state="processing", title=title, concepts=[], error="")

    cmd = ["claude", "--dangerously-skip-permissions", "-p", f'/llmwiki-ingest --source-file "{sources_path}"']
    notify_msg = "Ingestion complete"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(VAULT))
        output = result.stdout

        # Extract concept names from summary table rows
        concepts = re.findall(r"\|\s*(.+?)\s*\|\s*(?:New|Enriched)\s*\|", output)
        count = len(concepts)
        notify_msg = f"{count} concepts added" if count else "Ingestion complete"

        if result.returncode == 0:
            _set_status(state="done", concepts=concepts)
            append_log(title, url, f"success ({count} concepts)")
        else:
            error_detail = (result.stderr or "").strip().splitlines()[-1] if result.stderr else ""
            log.error("Claude stderr: %s", result.stderr)
            _set_status(state="error", error=f"Claude exited {result.returncode}" + (f": {error_detail}" if error_detail else ""))
            append_log(title, url, f"exit {result.returncode}")
    except subprocess.TimeoutExpired:
        notify_msg = "Ingestion timed out"
        _set_status(state="error", error="timed out after 300s")
        append_log(title, url, "timeout")
    except Exception as e:
        notify_msg = "Ingestion error"
        _set_status(state="error", error=str(e))
        append_log(title, url, f"error: {e}")
        log.error("Claude subprocess error: %s", e)

    subprocess.run(
        ["osascript", "-e", f'display notification "{notify_msg}" with title "LLMwiki"'],
        check=False,
    )


class IngestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress default access log
        log.info(fmt, *args)

    def _send_json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path != "/status":
            self._send_json(404, {"error": "not found"})
            return
        self._send_json(200, _get_status())

    def do_POST(self):
        if self.path != "/ingest":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "invalid JSON"})
            return

        title = body.get("title", "").strip()
        url = body.get("url", "").strip()
        note = body.get("note", "")
        highlights = body.get("highlights", [])
        source_type = body.get("type", "article")

        if source_type == "youtube":
            if not title or not url:
                self._send_json(400, {"error": "missing required fields: title, url"})
                return

            if find_existing_url(url):
                self._send_json(409, {"error": "URL already saved"})
                return

            try:
                content = extract_youtube_transcript(url)
            except Exception as e:
                log.error("YouTube transcript extraction failed for %s: %s", url, e)
                self._send_json(502, {"error": "No transcript available for this video"})
                return
        elif source_type == "pdf":
            if not title or not url:
                self._send_json(400, {"error": "missing required fields: title, url"})
                return

            if find_existing_url(url):
                self._send_json(409, {"error": "URL already saved"})
                return

            try:
                content = extract_pdf_text(url)
            except Exception as e:
                log.error("PDF extraction failed for %s: %s", url, e)
                self._send_json(502, {"error": "pdf extraction failed"})
                return
        else:
            content = body.get("content", "").strip()
            if not title or not url or not content:
                self._send_json(400, {"error": "missing required fields: title, url, content"})
                return

            if find_existing_url(url):
                self._send_json(409, {"error": "URL already saved"})
                return

        try:
            sources_path = write_sources_file(title, url, content, note, highlights, source_type)
        except Exception as e:
            log.error("Failed to write sources file: %s", e)
            self._send_json(500, {"error": "failed to write sources file"})
            return

        # Respond before Claude starts — non-blocking by design
        self._send_json(200, {"message": "saved", "path": str(sources_path)})

        append_log(title, url, "received")
        threading.Thread(
            target=trigger_claude, args=(sources_path, title, url), daemon=True
        ).start()


def main():
    claude_path = shutil.which("claude")
    if not claude_path:
        log.error(
            "'claude' not found on PATH — bridge server requires the claude CLI. Exiting."
        )
        raise SystemExit(1)
    log.info("Found claude at: %s", claude_path)

    server = http.server.HTTPServer(("localhost", PORT), IngestHandler)
    log.info("LLMwiki bridge server listening on localhost:%d", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
