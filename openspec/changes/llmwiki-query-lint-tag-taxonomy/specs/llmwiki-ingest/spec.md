## ADDED Requirements

### Requirement: Tag assignment on entry creation

When creating a new wiki entry, the skill SHALL assign one or more tags from the canonical tag vocabulary defined in `~/LLMwiki/CLAUDE.md`. Tags SHALL be written as YAML frontmatter at the top of the entry file.

#### Scenario: New entry has frontmatter tags

- **WHEN** the skill creates a new wiki entry for an extracted concept
- **THEN** the file begins with a YAML frontmatter block containing a `tags:` key with at least one value from the canonical taxonomy

##### Example: Tag assignment

- **GIVEN** canonical tags include `strategy`, `execution`, `frameworks`
- **WHEN** a new entry for "Portfolio Of Growth Engines" is created
- **THEN** the file starts with `---\ntags: [strategy, frameworks]\n---`

---

### Requirement: Tag update on entry enrichment

When enriching an existing wiki entry that lacks frontmatter tags, the skill SHALL add a `tags:` frontmatter block. If the entry already has frontmatter tags, the skill SHALL preserve existing tags and MAY add tags if clearly applicable based on the new source.

#### Scenario: Enriched entry gains tags when previously untagged

- **WHEN** the skill enriches an existing entry that has no YAML frontmatter
- **THEN** a frontmatter block with `tags:` is added at the top of the file

#### Scenario: Enriched entry preserves existing tags

- **WHEN** the skill enriches an existing entry that already has a `tags:` frontmatter key
- **THEN** the existing tags are preserved and not removed
