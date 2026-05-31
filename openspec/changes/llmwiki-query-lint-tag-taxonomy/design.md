## Context

The LLMwiki vault (`~/LLMwiki/`) is a personal compounding knowledge base driven by three operations defined in the vault's `CLAUDE.md`: Ingest, Query, and Lint. Only Ingest has a Claude skill backing it (`~/.claude/skills/llmwiki-ingest/`). Query and Lint exist as governance rules but have no executable implementation.

Skills in this system are invoked by the user via `claude` CLI from the vault root (`cd ~/LLMwiki && claude`, then `/skillname`). The bridge server is not involved — query and lint are user-initiated, not extension-triggered.

Current vault state: 30+ atomic wiki entries (flat root), `sources/` folder (immutable raw content), `LLMwiki Index.md` (grouped index), `CLAUDE.md` (governance). Wiki entries currently have no YAML frontmatter.

## Goals / Non-Goals

**Goals:**

- A `/llmwiki-query` skill that grounds answers in vault content with wikilink citations
- A `/llmwiki-lint` skill that audits vault health without modifying anything
- A tag taxonomy declared in `~/LLMwiki/CLAUDE.md` with tags applied retroactively to all existing entries
- Explicit "never do" constraints collected in `~/LLMwiki/CLAUDE.md`
- `llmwiki-ingest` REFERENCE.md updated so future entries carry tags from day one

**Non-Goals:**

- Scheduled/automated lint execution (can be layered later via launchd)
- Semantic embedding search (keyword + wikilink traversal sufficient for v1)
- Daily notes, project tracking, or temporal vault structure
- Bridge server or Chrome extension changes
- Multi-vault support

## Decisions

### Query grounds answers in vault content only

The query skill reads relevant wiki entries and synthesizes an answer from them. If no relevant entries exist, it reports that explicitly rather than falling back to Claude's training data. This enforces the system's core value: personal curated knowledge over generic LLM output.

*Alternative considered*: Hybrid mode (vault + training data). Rejected — would undermine the user's trust in whether answers came from their own thinking or the LLM.

### Lint reports only — never modifies

Lint produces a structured report with three sections (orphaned, missing, contradictions) and a count summary. It never renames, moves, or deletes files. All remediation is the user's decision.

*Alternative considered*: Auto-fix orphaned entries by adding placeholder backlinks. Rejected — users may have intentionally isolated entries; auto-modification erodes trust.

### Tag taxonomy derived from existing Index categories

The tag vocabulary is derived from the existing `LLMwiki Index.md` category groupings (Strategy, Planning, Communication, Knowledge Management) rather than inventing new terms. This avoids abstraction drift and lets the taxonomy bootstrap from already-curated structure.

### Tags as YAML frontmatter on wiki entries

Each wiki entry gains a YAML frontmatter block with a `tags:` list. Sources files are immutable — they receive no changes. The Index file is not tagged (it's a navigation artifact, not a concept entry).

### Retroactive batch tagging via a one-time ingest skill invocation

Existing entries are tagged in a single pass using a dedicated instruction in REFERENCE.md (or a one-time direct Claude invocation). This is not a new skill — it's a maintenance operation the user runs once.

### CLAUDE.md receives two additive sections only

`~/LLMwiki/CLAUDE.md` gains `## Tags` (taxonomy vocabulary) and `## Never do` (explicit prohibitions). Existing sections are unchanged to avoid disrupting the ingest skill which reads this file.

## Implementation Contract

### `/llmwiki-query` skill

**Behavior**: User invokes `/llmwiki-query <question>` from `~/LLMwiki`. Skill reads all `*.md` files in vault root (excluding Index, CLAUDE.md), identifies relevant entries by concept match, synthesizes a grounded answer in prose, and lists sources with `[[wikilinks]]`. Optionally creates a new wiki entry from the answer if user confirms.

**Command**: Invoked as a Claude skill from vault root. No subprocess, no bridge.

**Answer format**:
```
[synthesized prose answer with inline [[wikilinks]] to cited entries]

Sources used:
- [[Entry Name One]]
- [[Entry Name Two]]
```

**Fallback**: If no relevant entries found → "No relevant entries found in vault for this question."

**Optional filing**: After answer, skill asks "File this answer as a new wiki entry? (y/n)". If yes, creates entry following standard format from `REFERENCE.md`, with `## Sources` linking to the entries it synthesized from.

**Acceptance criteria**: Invoke with a question known to have relevant entries → answer contains `[[wikilinks]]` to existing files. Invoke with an off-topic question → explicit "no relevant entries" message, no hallucinated citations.

**Scope boundaries**: In scope — vault-only answers, optional entry creation. Out of scope — web search, PDF/sources content (sources are raw text, not processed concepts).

---

### `/llmwiki-lint` skill

**Behavior**: User invokes `/llmwiki-lint` from `~/LLMwiki`. Skill scans all `*.md` files in vault root, produces a structured report in three sections, never modifies any file.

**Report format**:
```
## Lint Report

### Orphaned Entries
Entries with no outbound [[wikilinks]] AND no inbound links from any other entry:
- [[Entry Name]] — no links in or out

### Missing Pages
[[wikilinks]] referenced in entries that have no corresponding .md file:
- [[Concept Name]] — referenced in: [[Entry A]], [[Entry B]]

### Contradiction Signals
Entries making potentially opposing claims (heuristic — verify manually):
- [[Entry A]] ↔ [[Entry B]] — both reference [[Shared Concept]] with differing assertions

---
Summary: N orphaned | M missing pages | K contradictions flagged
```

**Failure modes**: If vault root has no `*.md` files → "Vault appears empty." No errors thrown for entries with no wikilinks that DO have inbound links (those are valid leaf entries).

**Acceptance criteria**: Add a test entry with no wikilinks and no inbound links → appears in Orphaned. Add a `[[Nonexistent Concept]]` wikilink to any entry → appears in Missing Pages. Run lint → no files modified.

**Scope boundaries**: In scope — vault root `*.md` files only. Out of scope — `sources/` folder, `LLMwiki Index.md` (navigation artifact, not a concept entry), `CLAUDE.md`.

---

### Tag taxonomy in `~/LLMwiki/CLAUDE.md`

**Behavior**: A `## Tags` section added to `CLAUDE.md` listing canonical tag names and their meanings. All wiki entries gain YAML frontmatter with `tags: [...]`.

**Frontmatter format** (added to top of each wiki entry):
```yaml
---
tags: [strategy, frameworks]
---
```

**Tag vocabulary** (initial, derived from Index categories):
- `strategy` — high-level direction, competitive positioning
- `execution` — planning, delivery, project management
- `communication` — presentations, messaging, stakeholder alignment
- `knowledge-management` — how to capture, organize, and retrieve knowledge
- `frameworks` — reusable mental models and structured approaches
- `principles` — durable rules of thumb, beliefs about how the world works
- `mental-models` — cognitive tools for reasoning about complex systems

**Acceptance criteria**: After batch tagging pass, every `~/LLMwiki/*.md` file (excluding Index, CLAUDE.md) has a `tags:` YAML frontmatter key with at least one value from the taxonomy.

---

### `llmwiki-ingest` REFERENCE.md update

**Behavior**: Tag assignment step added to both "create new entry" and "enrich existing entry" instructions. New entries get tags from taxonomy at creation time. Enriched entries get tags updated/added if not already present.

**Acceptance criteria**: Ingest a new article → resulting wiki entry has `tags:` frontmatter.

---

### `~/LLMwiki/CLAUDE.md` — `## Never do` section

**Behavior**: Explicit prohibition list added as a new section.

**Content**:
- Never delete any file in the vault
- Never modify files in `sources/` (they are immutable archives)
- Never create a wiki entry without first checking if it already exists
- Never auto-resolve contradictions between entries
- Never overwrite user-edited frontmatter without confirmation

**Acceptance criteria**: Section exists in CLAUDE.md, readable by any Claude operation on the vault.

## Risks / Trade-offs

[Contradiction detection is heuristic] → The lint skill uses wikilink co-occurrence as a proxy for contradiction (two entries referencing the same concept with differing assertions). This will produce false positives. Mitigation: label section clearly as "Contradiction Signals" (not "Contradictions"), and note "verify manually" in the report.

[Batch frontmatter tagging modifies many files at once] → If the tagging pass is interrupted, the vault is left in a partially-tagged state. Mitigation: the skill should process entries one by one and report progress; partial tagging is still valid (lint and query can handle mixed frontmatter/no-frontmatter states).

[CLAUDE.md edits could break ingest skill] → The ingest skill reads `CLAUDE.md` at runtime. Additive sections (Tags, Never do) at the end of the file are safe. Mitigation: append-only edits, no modifications to existing sections.
