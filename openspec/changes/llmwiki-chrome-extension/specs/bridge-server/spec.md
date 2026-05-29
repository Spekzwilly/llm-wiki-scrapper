## ADDED Requirements

### Requirement: Bridge server accepts ingest requests

The bridge server SHALL listen on `localhost:7842` and accept `POST /ingest` requests with a JSON body containing `title`, `url`, `content`, `highlights`, and `note` fields. Requests missing `title`, `url`, or `content` SHALL be rejected with `400 Bad Request`.

#### Scenario: Valid request accepted

- **WHEN** a POST to `/ingest` is made with all required fields
- **THEN** the server returns `200 OK` immediately after writing the sources file

#### Scenario: Missing required field

- **WHEN** a POST to `/ingest` is missing `title`, `url`, or `content`
- **THEN** the server returns `400 Bad Request`

---

### Requirement: Duplicate URL detection

Before writing a new sources file, the bridge server SHALL scan all files in `~/LLMwiki/sources/` for a matching `url:` frontmatter value. If a match is found, the server SHALL return `409 Conflict` and SHALL NOT write a new file.

#### Scenario: Duplicate detected

- **WHEN** the submitted URL matches the `url:` field in an existing sources file
- **THEN** the server returns `409 Conflict`
- **AND** no new file is written

#### Scenario: New URL proceeds

- **WHEN** the submitted URL does not match any existing sources file
- **THEN** the server proceeds to write the sources file

---

### Requirement: Sources file written to vault

The bridge server SHALL write the received content to `~/LLMwiki/sources/<Title>.md` where `<Title>` is the article title converted to Title Case with special characters removed. The file SHALL contain YAML frontmatter followed by the article body. Content SHALL be truncated to 50,000 characters if longer.

#### Scenario: Sources file created with correct frontmatter

- **WHEN** a valid POST is received
- **THEN** a file is created at `~/LLMwiki/sources/<Title>.md` with frontmatter containing `title`, `url`, `saved` (ISO date), `type: article`, `personal-note`, and `highlights` fields

##### Example: frontmatter shape

- **GIVEN** payload `{title: "My Article", url: "https://example.com", note: "interesting", highlights: ["key insight"], content: "..."}`
- **WHEN** the server writes the sources file
- **THEN** the frontmatter contains:
  ```
  title: My Article
  url: https://example.com
  saved: 2026-05-28
  type: article
  personal-note: interesting
  highlights:
    - key insight
  ```

---

### Requirement: Claude CLI triggered as background process

After writing the sources file, the bridge server SHALL invoke the `claude` CLI as a non-blocking subprocess with the llmwiki-ingest skill and the sources file path. The HTTP response SHALL be sent before the subprocess completes.

#### Scenario: Claude triggered after file write

- **WHEN** the sources file is written successfully
- **THEN** the server returns `200 OK` to the client
- **AND** `claude` is spawned as a background subprocess

#### Scenario: Claude not found on PATH

- **WHEN** `claude` is not available on PATH at server startup
- **THEN** the server logs a clear error message and SHALL NOT start

---

### Requirement: macOS notification sent on completion

The bridge server SHALL send a macOS system notification via `osascript` after the Claude subprocess exits, displaying the number of concepts added or enriched.

#### Scenario: Notification on success

- **WHEN** the Claude subprocess exits with code 0
- **THEN** a macOS notification is sent with title "LLMwiki" and body "N concepts added"

---

### Requirement: Activity logged to file

The bridge server SHALL append one log entry per ingestion to `~/LLMwiki/bridge.log` containing timestamp, article title, URL, and outcome.

#### Scenario: Log entry written

- **WHEN** an ingestion completes (success or error)
- **THEN** a timestamped line is appended to `~/LLMwiki/bridge.log`
