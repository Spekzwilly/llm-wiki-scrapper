# llmwiki-ingest Spec

## Overview

The `llmwiki-ingest` skill ingests an article into the LLMwiki Obsidian vault at `~/LLMwiki/`. It fetches raw article content, saves it to `sources/`, extracts atomic concepts, and creates or enriches wiki entries.

---

## Requirements

### Requirement: Accept source file argument

The skill SHALL accept an optional argument specifying a local sources file path. In the current implementation, this argument is not supported — the skill always fetches content from a URL via WebFetch.

#### Scenario: No source file argument — URL fetch used

- **WHEN** the skill is invoked with a URL and no source file path argument
- **THEN** the skill fetches the article via WebFetch
- **AND** saves the result to `~/LLMwiki/sources/`

---

### Requirement: Sources file check before fetch

Before fetching a URL, the skill SHALL check `~/LLMwiki/sources/` for an existing file whose `url:` frontmatter matches the submitted URL. If a match is found, the skill SHALL use the existing file and skip the WebFetch step.

#### Scenario: Existing sources file reused

- **WHEN** the skill is invoked with a URL that matches an existing sources file
- **THEN** the skill reads from the existing file
- **AND** no network fetch is performed

#### Scenario: No existing sources file triggers fetch

- **WHEN** the skill is invoked with a URL that has no matching sources file
- **THEN** the skill fetches the article via WebFetch

---

### Requirement: Raw content saved to sources/

The skill SHALL save raw article content to `~/LLMwiki/sources/<Title>.md` with YAML frontmatter containing `title`, `url`, `saved` (ISO date), `type`, and `personal-note` fields, followed by the article body.

#### Scenario: Sources file created after fetch

- **WHEN** the skill successfully fetches an article
- **THEN** a file is created at `~/LLMwiki/sources/<Title>.md` with correct frontmatter

---

### Requirement: Atomic concept extraction

The skill SHALL analyze the article content and extract discrete, reusable concepts — each representing a single idea that can be applied independently of the source article. Concepts SHALL be named in Title Case and be role-agnostic (applicable across domains, not PM-specific).

#### Scenario: Multiple concepts extracted from one article

- **WHEN** an article covers multiple independent ideas
- **THEN** each idea is extracted as a separate wiki entry
- **AND** each entry has a Title Case filename

---

### Requirement: Wiki entry created or enriched

For each extracted concept, the skill SHALL check whether a wiki entry already exists in `~/LLMwiki/`. If it does not exist, a new entry SHALL be created. If it already exists, the entry SHALL be enriched with new evidence, examples, or "When to apply" context from the new article.

#### Scenario: New concept creates new entry

- **WHEN** no wiki file exists for the extracted concept
- **THEN** a new `.md` file is created in `~/LLMwiki/` with sections: concept definition, when to apply, evidence, and sources

#### Scenario: Existing concept is enriched

- **WHEN** a wiki file already exists for the extracted concept
- **THEN** the file is updated with additional evidence or context
- **AND** the original content is preserved

---

### Requirement: Index updated

After all entries are created or enriched, the skill SHALL update `~/LLMwiki/LLMwiki Index.md` to include any new entries under the appropriate section heading.

#### Scenario: New entry added to index

- **WHEN** a new wiki entry is created
- **THEN** the entry title appears in `LLMwiki Index.md`

---

### Requirement: Summary reported

After completing ingestion, the skill SHALL display a summary table listing each concept, whether it was created or enriched, and the source article title.

#### Scenario: Summary shown after ingestion

- **WHEN** ingestion completes
- **THEN** a markdown table is displayed with columns: Concept, Action (Created/Enriched), Source
