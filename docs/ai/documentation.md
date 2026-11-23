# Documentation

How the user documentation in `docs/` is written.

## Pages

- `docs/explanations/` is for readers who know propulsion: concept and equations first,
  each equation with its source and number, an "Implemented in" link to the code as a
  mkdocstrings cross-reference, and `References` with editions at the end. No code
  listings. `docs/explanations/thrust.md` shows the format.
- `docs/api/` has one page per module: a short paragraph, then `::: machwave.<module>`.
  The rest comes from the docstrings, so fix a docstring instead of repeating it on the
  page.
- Add every new page to `nav` in `mkdocs.yml`. A page left out of `nav` still builds,
  even with `--strict`, but readers cannot reach it.

## Style

- Short, plain sentences in English. No rhetorical openers, no "X, not Y" contrasts, no
  heavy bolding.
- A grain geometry is not "analytical": BATES is computed in closed form and the others
  with the fast marching method, as an implementation choice.

## Keeping it current

- Docstrings and explanation pages change in the same change that alters the behaviour
  they describe.
