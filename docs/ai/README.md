# Agent docs

Where a rule for coding agents goes in this repository. `AGENTS.md` is the map: the
commands, how to verify, the caveats that apply everywhere, and which file here to read
for which paths. Each file here covers one kind of work. They are excluded from the
published site in `mkdocs.yml`.

## What belongs here

- Only what an agent cannot infer from the code: the rule, the reason when it is not
  obvious, and one file that shows it.
- A rule needs evidence: it appears in more than one place, or a test, a base class or a
  `make` target enforces it. If a tool can enforce it, enforce it there and name the
  command instead of restating the rule.
- Leave out general engineering advice, lists of classes or files, and descriptions of
  what the code already shows.
- The test: adding a grain geometry or a loss component should not need a doc change.
  Changing a pattern should.

## Where a new rule goes

- It applies to the whole repository: `AGENTS.md`, under "Important caveats".
- It applies to one kind of work: the matching file here.
- It is a new kind of work with several rules: a new file here, plus a line under
  "Before you edit" in `AGENTS.md`.

## Keeping them true

- These files change in the same change that alters the pattern they describe.
- One home per rule. Other files link to it instead of repeating it.
- Where the code does not yet follow a rule, the file says so. Write new code to the
  rule, and do not refactor old code to it as a side effect of unrelated work. Remove
  the note in the change that makes the code follow the rule.
