<!--
Each task description MUST state:
- the behavior or contract being delivered (what is observably true when the
  task is complete), and
- the verification target that proves completion (test, CLI invocation,
  analyzer check, manual assertion, or content review).

File paths are supporting context for locating the work, never the task
itself. "Edit file X" is not a valid task — it is missing both behavior and
verification.
-->

## 1. Vault Governance — CLAUDE.md Updates

- [x] 1.1 Implement tag taxonomy in `~/LLMwiki/CLAUDE.md`: add `## Tags` section declaring the canonical tag vocabulary (strategy, execution, communication, knowledge-management, frameworks, principles, mental-models). Tag taxonomy derived from existing Index categories. CLAUDE.md receives two additive sections only — existing sections are not touched. Verify: open `~/LLMwiki/CLAUDE.md` and confirm `## Tags` section exists with all seven tag names defined.
- [x] 1.2 Add `~/LLMwiki/CLAUDE.md` — `## Never do` section — listing explicit prohibitions (never delete files, never modify sources/, never create entry without checking duplicates, never auto-resolve contradictions, never overwrite user-edited frontmatter without confirmation). Verify: open `~/LLMwiki/CLAUDE.md` and confirm `## Never do` section exists with all five prohibitions listed.

## 2. Tag Taxonomy Rollout

- [x] 2.1 Apply retroactive batch tagging via a one-time ingest skill invocation (or direct Claude operation) — adds `tags:` YAML frontmatter to all existing `~/LLMwiki/*.md` files (excluding Index, CLAUDE.md). Tags as YAML frontmatter on wiki entries: each entry SHALL gain `---\ntags: [...]\n---` at top with at least one value from the canonical taxonomy. Verify: check five representative wiki entries — each has a `tags:` YAML frontmatter block with valid taxonomy values.
- [x] 2.2 `llmwiki-ingest` REFERENCE.md update: add tag assignment steps to both "create new entry" and "enrich existing entry" instructions — tag assignment on entry creation and tag update on entry enrichment are now required steps. Verify: read the updated REFERENCE.md and confirm tag assignment instructions appear in both create and enrich sections.

## 3. Build /llmwiki-query Skill

- [x] 3.1 Build `/llmwiki-query` skill at `~/.claude/skills/llmwiki-query/SKILL.md` implementing vault-grounded question answering: reads all `*.md` files in vault root (scope boundary — sources/, Index, CLAUDE.md excluded), selects relevant entries by concept match, synthesizes prose answer with inline `[[wikilinks]]`, appends "Sources used:" section. Query grounds answers in vault content only — if no relevant entries exist, responds "No relevant entries found in vault for this question." Verify: invoke `/llmwiki-query` with a question known to match an existing entry → answer contains at least one `[[wikilink]]` to a real file; invoke with off-topic question → "No relevant entries found" message, no fabricated citations.
- [x] 3.2 Add optional answer filing as new wiki entry to the query skill: after delivering an answer citing at least one entry, skill asks "File this answer as a new wiki entry? (y/n)". If confirmed, creates entry in `~/LLMwiki/` root following standard format with `## Sources` linking to cited entries. No filing prompt appears when vault has no relevant entries. Verify: answer a question, respond "y" → new entry file exists in vault root with `## Sources` section; respond "n" → no file written.
- [x] 3.3 Confirm working directory contract for query skill: skill resolves all paths relative to `~/LLMwiki/`, consistent with how `/llmwiki-ingest` operates. Verify: invoke `/llmwiki-query` from `~/LLMwiki` via `claude` CLI → skill finds vault entries without absolute path errors.

## 4. Build /llmwiki-lint Skill

- [x] 4.1 Build `/llmwiki-lint` skill at `~/.claude/skills/llmwiki-lint/SKILL.md` implementing orphaned entry detection. Lint reports only — never modifies vault files. Identifies `*.md` files in vault root with no outbound `[[wikilinks]]` AND no inbound links from any other entry. Leaf entries (no outbound, but referenced inbound) SHALL NOT be flagged. Verify: add a test entry with no wikilinks and no inbound links → it appears in "Orphaned Entries" section; remove test entry after verification.
- [x] 4.2 Implement missing page detection in the lint skill: identifies `[[wikilinks]]` in wiki entries that have no corresponding `.md` file in vault root. Report lists the missing concept and all entries that reference it. Verify: add `[[NonexistentConcept]]` to any entry → "NonexistentConcept" appears in "Missing Pages" section with the referencing entry listed.
- [x] 4.3 Implement contradiction signal detection (heuristic) in the lint skill: identifies pairs of entries that reference the same `[[wikilink]]` and contain opposing-assertion language markers. Each flagged pair MUST carry "verify manually" annotation. Verify: confirm report section is labeled "Contradiction Signals" (not "Contradictions") and each entry carries the "verify manually" note.
- [x] 4.4 Enforce read-only audit contract: lint skill SHALL NOT modify, rename, delete, or create any file at any point. Verify: run `/llmwiki-lint` on live vault, then `git status` in `~/LLMwiki/` (or check file mtimes) — no files modified.
- [x] 4.5 Implement structured report with count summary: output has three labelled sections (Orphaned Entries, Missing Pages, Contradiction Signals), each showing "None found." when empty. Final line reads `Summary: N orphaned | M missing pages | K contradictions flagged`. Verify: run lint on clean vault → all three sections present with "None found." and summary line shows "0 orphaned | 0 missing pages | 0 contradictions flagged".

## 5. Verification Pass

- [x] 5.1 End-to-end query verification: ingest a new article, then invoke `/llmwiki-query` with a question relevant to one of the extracted concepts → answer cites the new entry via `[[wikilink]]`. Confirm no citations to non-existent files appear in the answer.
- [x] 5.2 End-to-end lint verification: run `/llmwiki-lint` on the full live vault → report displays all three sections, summary line is present, no vault files were modified during the run.
- [x] 5.3 Tag completeness check: confirm every `~/LLMwiki/*.md` file in vault root (excluding Index and CLAUDE.md) has a `tags:` frontmatter key, and all tag values are from the canonical vocabulary declared in `CLAUDE.md`.
