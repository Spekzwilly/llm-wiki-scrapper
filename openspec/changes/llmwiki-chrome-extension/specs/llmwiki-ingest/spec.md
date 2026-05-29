## MODIFIED Requirements

### Requirement: Accept source file argument

The llmwiki-ingest skill SHALL accept an optional `--source-file <path>` argument. When provided, the skill SHALL read article content from the local file instead of fetching the URL via WebFetch. The sources file check (step 1 of the workflow) SHALL be skipped since the file already exists.

#### Scenario: Source file argument skips fetch

- **WHEN** the skill is invoked with `--source-file ~/LLMwiki/sources/Article.md`
- **THEN** the skill reads content from the local file
- **AND** WebFetch is not called

#### Scenario: No argument falls back to URL fetch

- **WHEN** the skill is invoked with a URL and no `--source-file` argument
- **THEN** the existing fetch-and-save workflow runs unchanged

---

## ADDED Requirements

### Requirement: Highlights used as extraction signal

When the sources file frontmatter contains a `highlights` list, the skill SHALL treat those passages as weighted extraction signal. Concepts that appear in or are closely related to highlighted passages SHALL be extracted first and SHALL receive richer "When to apply" sections than non-highlighted concepts.

#### Scenario: Highlighted concept prioritized

- **WHEN** a sources file contains highlights referencing a concept
- **THEN** that concept appears in the extraction output
- **AND** its "When to apply" section reflects the context of the highlight

#### Scenario: No highlights falls back to full judgment

- **WHEN** the `highlights` frontmatter field is empty or absent
- **THEN** the skill applies its standard full-article extraction judgment unchanged
