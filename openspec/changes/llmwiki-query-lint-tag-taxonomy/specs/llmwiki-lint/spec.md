## ADDED Requirements

### Requirement: Orphaned entry detection

The skill SHALL identify wiki entries that have no outbound `[[wikilinks]]` to other entries AND receive no inbound `[[wikilinks]]` from any other entry. These are considered orphaned.

#### Scenario: Orphaned entry detected

- **WHEN** a wiki entry `*.md` file contains no `[[wikilink]]` patterns AND no other entry contains a `[[wikilink]]` pointing to it
- **THEN** the entry appears in the "Orphaned Entries" section of the lint report

#### Scenario: Leaf entry not flagged

- **WHEN** a wiki entry has no outbound wikilinks but IS referenced by at least one other entry
- **THEN** it SHALL NOT appear in the Orphaned Entries section (it is a valid leaf node)

#### Scenario: Scope boundary

- **WHEN** the skill scans the vault
- **THEN** it SHALL inspect only `*.md` files in the vault root, excluding `sources/`, `LLMwiki Index.md`, and `CLAUDE.md`

---

### Requirement: Missing page detection

The skill SHALL identify `[[wikilinks]]` that appear in wiki entries but have no corresponding `.md` file in the vault root.

#### Scenario: Missing page found

- **WHEN** any wiki entry contains `[[Concept Name]]` and no file named `Concept Name.md` exists in `~/LLMwiki/`
- **THEN** "Concept Name" appears in the "Missing Pages" section with a list of entries that reference it

##### Example: Multiple referencing entries

- **GIVEN** entries `A.md` and `B.md` both contain `[[Shared Concept]]` and `Shared Concept.md` does not exist
- **WHEN** lint runs
- **THEN** Missing Pages section lists: `[[Shared Concept]] — referenced in: [[A]], [[B]]`

#### Scenario: Existing page not flagged

- **WHEN** a wikilink target has a matching `.md` file in the vault root
- **THEN** it SHALL NOT appear in the Missing Pages section

---

### Requirement: Contradiction signal detection

The skill SHALL identify pairs of wiki entries that reference the same concept via wikilink and contain language suggesting opposing assertions. This detection is heuristic and the report MUST label findings as "signals" requiring manual verification.

#### Scenario: Contradiction signal flagged

- **WHEN** two entries both reference the same `[[Shared Concept]]` and contain linguistic markers of opposition (e.g., "not", "instead", "unlike", "contrary")
- **THEN** the pair appears in the "Contradiction Signals" section with a note to verify manually

#### Scenario: No false guarantee

- **WHEN** the Contradiction Signals section is non-empty
- **THEN** each entry in that section MUST carry the annotation "verify manually" to make clear the detection is heuristic, not definitive

---

### Requirement: Read-only audit

The skill SHALL NOT modify, rename, delete, or create any file in the vault at any point during or after the audit.

#### Scenario: Vault state unchanged after lint

- **WHEN** `/llmwiki-lint` completes
- **THEN** every file in `~/LLMwiki/` is byte-for-byte identical to its pre-lint state

---

### Requirement: Structured report with count summary

The skill SHALL output a report with three labelled sections (Orphaned Entries, Missing Pages, Contradiction Signals) and a final summary line.

#### Scenario: Summary line format

- **WHEN** lint completes
- **THEN** the final line of the report reads: `Summary: N orphaned | M missing pages | K contradictions flagged` where N, M, K are integer counts

#### Scenario: Empty section

- **WHEN** no issues are found in a category
- **THEN** the section still appears in the report with the text "None found."

##### Example: Clean vault

- **GIVEN** all entries have wikilinks, all wikilink targets exist, no contradiction signals detected
- **WHEN** lint runs
- **THEN** report shows all three sections with "None found." and summary reads "Summary: 0 orphaned | 0 missing pages | 0 contradictions flagged"
