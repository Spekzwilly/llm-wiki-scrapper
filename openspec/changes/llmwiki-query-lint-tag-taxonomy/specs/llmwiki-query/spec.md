## ADDED Requirements

### Requirement: Vault-grounded question answering

The skill SHALL accept a natural language question and synthesize an answer drawn exclusively from wiki entries in the `~/LLMwiki/` vault root. The answer SHALL cite every entry it draws from using `[[wikilink]]` notation. The skill SHALL NOT incorporate Claude training data as a source for the answer body.

#### Scenario: Question with relevant entries

- **WHEN** the user invokes `/llmwiki-query` with a question that matches content in one or more wiki entries
- **THEN** the skill returns a prose answer with inline `[[wikilinks]]` to the specific entries used, followed by a "Sources used:" section listing all cited entries

##### Example: Single-concept question

- **GIVEN** vault contains `Portfolio Of Growth Engines.md` describing the concept of multiple growth bets
- **WHEN** user asks "What is a portfolio of growth engines?"
- **THEN** answer contains a prose explanation with `[[Portfolio Of Growth Engines]]` as an inline citation, and "Sources used: [[Portfolio Of Growth Engines]]" in the trailing section

#### Scenario: Question with no relevant entries

- **WHEN** the user invokes `/llmwiki-query` with a question for which no vault entries are relevant
- **THEN** the skill responds with "No relevant entries found in vault for this question." and does not produce a fabricated answer

#### Scenario: Scope boundary — sources folder excluded

- **WHEN** the skill searches for relevant content
- **THEN** it SHALL read only `*.md` files in the vault root, excluding `sources/`, `LLMwiki Index.md`, and `CLAUDE.md`

---

### Requirement: Optional answer filing as new wiki entry

After delivering an answer, the skill SHALL offer to create a new wiki entry from the synthesized answer if the answer is substantive (i.e., at least one entry was cited). The user MUST confirm before any file is written.

#### Scenario: User confirms filing

- **WHEN** the skill has produced an answer citing at least one entry AND the user responds affirmatively to the filing prompt
- **THEN** the skill creates a new `*.md` file in `~/LLMwiki/` root following the standard wiki entry format, with `## Sources` linking to the entries it synthesized from

#### Scenario: User declines filing

- **WHEN** the user responds negatively to the filing prompt
- **THEN** no file is written and the skill exits cleanly

#### Scenario: No filing prompt when vault has no relevant entries

- **WHEN** the skill returned "No relevant entries found"
- **THEN** the filing prompt SHALL NOT appear

---

### Requirement: Working directory

The skill SHALL be invoked from `~/LLMwiki` as the working directory, consistent with how `/llmwiki-ingest` is invoked.

#### Scenario: Correct working directory

- **WHEN** the user runs `claude` from `~/LLMwiki` and invokes `/llmwiki-query`
- **THEN** the skill resolves all file paths relative to `~/LLMwiki/`
