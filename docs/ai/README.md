# Agent docs

How the instructions for coding agents are organised in this repository, and where a new
rule goes. Read only what `AGENTS.md` routes you to. These files are excluded from the
published site in `mkdocs.yml`.

## The layers

- `AGENTS.md` is the map: what the repository is, which doc to read for which paths, the
  layout, the commands, how to verify, and the caveats that apply everywhere.
- `docs/ai/<topic>.md` is the manual for one kind of work, named after the work that
  triggers it.

## What belongs here

- The rule, the reason when it is not obvious, and one file that shows it.
- Only what an agent cannot infer from the code. A rule needs evidence: it appears in
  more than one place, or a test, a base class or a `make` target enforces it.
- Leave out general engineering advice, anything a tool already enforces, lists of
  classes or files, and status notes that will be wrong next month.
- The test: adding a grain geometry or a loss component should not need a doc change.
  Changing a pattern should.

## Where a new rule goes

- It applies to the whole repository: `AGENTS.md`, under "Important caveats".
- It applies to one kind of work: the matching `docs/ai` file.
- It is a new kind of work with several rules: a new `docs/ai/<topic>.md`, plus a line
  under "Before you edit" in `AGENTS.md`.
- It can be enforced by ruff, pyright, a test or a `make` target: enforce it there and
  name the command instead of restating the rule.

## Keeping them true

- Docs change in the same change that alters the pattern they describe. A doc that
  teaches the old pattern is a defect.
- One home per rule. Other files link to it instead of repeating it.
- Where the code does not yet follow a rule written here, the doc says so. Write new code
  to the rule, and do not refactor old code to it as a side effect of unrelated work.
