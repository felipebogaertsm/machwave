# Issues and pull requests

How to fill the forms in `.github/ISSUE_TEMPLATE/` and
`.github/PULL_REQUEST_TEMPLATE.md`. The forms give the sections. This file gives what
goes in them.

## Size

- A small change takes one to three sentences and the required sections.
- A bug, or a change to a physical model, a solver, the simulation loop or the public
  API, keeps every section that applies and follows the order below.

## Order of the explanation

1. The answer. One or two sentences with the cause and its consequence. A reader who
   stops here knows what breaks and why.
2. The mechanism. The chain from the governing equation or numerical property to the
   symptom. Give the equation, name each symbol on first use, and give the magnitudes
   that put this case where it fails.
3. The evidence. The case, its parameters and the exact error or value on the base
   branch. Use a table when several cases compare.
4. Why this fix. Each alternative a reviewer would ask about, and the reason, with
   its number, that rules it out.
5. The result. The same cases after the change: both values and the relative
   difference.

An issue covers 1 to 3, and 2 only when the cause is known.

## Writing

- One sentence per line and one fact per sentence. Periods over semicolons.
- Equations go in ```` ```math ```` blocks and inline math in `` $`...`$ ``. Never write
  a formula as code in prose.
- Standard propulsion terms: "biliquid", "characteristic length", "chamber filling
  time". Spell out a symbol or abbreviation on first use.
- A word like "stiff", "diverges" or "unstable" comes with the number and the mechanism
  behind it, or is left out.
- Every number carries its case, its unit and what it is compared with.
- Verification names the test that fails on the base branch and passes on the change,
  and the checks that ran. A count of passing tests is not evidence.
- Describe the behaviour, not the diff. No file lists or per-function changelogs. Name
  a function only where a reader has to find it, as in a breaking change.
- No rhetorical openers, "X, not Y" contrasts, heavy bolding or hedging.
