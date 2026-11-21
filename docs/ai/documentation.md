# Documentation

How the user documentation in `docs/` is written. Read this before editing `docs/` or
`mkdocs.yml`, or when a change alters public API or behaviour.

## Pages

- `docs/explanations/` is for readers who know propulsion. Concept and equations first,
  each equation with its source and number, e.g. "(Sutton & Biblarz, Eq. 3-30)". Each
  section ends with an "Implemented in" link to the function or class, written as a
  mkdocstrings cross-reference: ``[`name`][machwave.module.name]``. The page ends with
  `References`, with editions. No code listings. `docs/explanations/thrust.md` is the
  reference.
- `docs/api/` has one page per module: a short paragraph on what the module is for, then
  `::: machwave.<module>`. The API text comes from the docstrings, so fix a docstring
  instead of repeating it on the page.
- A new page is added to `nav` in `mkdocs.yml`; `make docs-deploy` builds with
  `--strict` and fails on broken links.
- Math uses `$...$` and `$$...$$` (arithmatex with MathJax).

## Style

- Short, plain sentences in English. No rhetorical openers, no "X, not Y" contrasts, no
  heavy bolding.
- Use the same word for a concept as the code, results and plots.

## Keeping it current

- Docstrings, explanation pages and `docs/ai/` change in the same change that alters the
  pattern or behaviour they describe. A doc that teaches the old behaviour is a defect.
