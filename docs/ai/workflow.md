# Workflow

## Issues

- Titles and bodies use standard propulsion terms. Spell out a quantity on first use with
  its symbol in parentheses, then use the symbol: thrust coefficient (C_F),
  characteristic velocity (c*), specific impulse (Isp), mixture ratio (O/F), chamber
  pressure (Pc). Opaque acronyms for engine types are not allowed.
- The engine type is "biliquid".
- Plain technical wording; no software or accounting metaphors.
- Bodies are one or two sentences pointing at the relevant code, unless the work needs a
  real specification.
- An issue that bundles independent bugs is split into one sub-issue per bug.

## Branches

- One branch per issue, named `{issue_number}-short-summary`, for example
  `207-flatten-motor-step`.
- One pull request per branch. Independent bugs get separate branches with disjoint file
  sets, so they merge in any order.

## Commits

- The subject states the behaviour change in the imperative, in plain words.
- The body explains the physical or numerical mechanism and the measured symptom, with
  numbers and units where they exist.
- Stage files by explicit path.
- No attribution lines of any tool or assistant.

## Pull requests

- Title as the commit subject. The body is short and starts with `Closes #<issue>.`
- Fill in the template, including the physical model checklist when a model changed.
- Say what was verified and how, and what could not be run.
- No attribution lines of any tool or assistant.

## Everywhere

- Never abbreviate, in issues, commits, pull requests and code alike.
- Issue and pull request numbers belong in branch names, commit messages and pull
  requests, never in source files, docstrings or tests.
