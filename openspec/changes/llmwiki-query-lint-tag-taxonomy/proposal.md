## Why

The LLMwiki vault implements Karpathy's three-operation framework (Ingest, Query, Lint) but only Ingest has a working skill — meaning the user cannot search their accumulated knowledge or detect quality issues as the vault grows. Additionally, wiki entries lack machine-readable frontmatter tags, blocking batch operations and filtering.

## What Changes

- New `/llmwiki-query` skill: natural language search over vault wiki entries, grounded answer with wikilink citations, optional filing of answer as a new wiki entry
- New `/llmwiki-lint` skill: vault audit for orphaned entries, missing pages (wikilinked but no file), and contradiction signals — outputs structured report, never auto-modifies
- Tag taxonomy declared in `~/LLMwiki/CLAUDE.md` with a `## Tags` vocabulary section
- YAML frontmatter `tags:` field added to all wiki entries (new and retroactively to existing)
- Explicit `## Never do` section added to `~/LLMwiki/CLAUDE.md`
- `llmwiki-ingest` skill's `REFERENCE.md` updated to include tag assignment in create/enrich steps

## Capabilities

### New Capabilities

- `llmwiki-query`: Claude skill that searches vault wiki entries by relevance, synthesizes a grounded answer with wikilink citations, and optionally creates a new wiki entry from the answer
- `llmwiki-lint`: Claude skill that audits the vault for orphaned entries, missing pages, and contradiction signals — outputs a structured report with count summary

### Modified Capabilities

- `llmwiki-ingest`: Tag assignment added to entry creation and enrichment steps in REFERENCE.md

## Impact

- Affected code: `~/.claude/skills/llmwiki-query/SKILL.md` (new), `~/.claude/skills/llmwiki-lint/SKILL.md` (new), `~/.claude/skills/llmwiki-ingest/REFERENCE.md` (updated), `~/LLMwiki/CLAUDE.md` (updated), all `~/LLMwiki/*.md` wiki entries (frontmatter added)
- No changes to bridge server, Chrome extension, or launchd service
- No new dependencies
