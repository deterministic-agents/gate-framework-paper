# GATE Framework Paper

Source for the *Governed Agent Trust Environment* (GATE) framework paper,
version 1.4. Built with [Quarto](https://quarto.org) as a book that renders
to both PDF and HTML from a single markdown source of truth.

## Build

```
quarto render
```

Outputs:

- HTML book: `_book/index.html`
- PDF book:  `_book/GATE-v1.4.pdf`

Render a single format:

```
quarto render --to html
quarto render --to pdf
```

## Source authority

The control sections in `chapters/04-controls-layer-1.qmd` through
`chapters/07-controls-layer-4.qmd` render from the on-disk control specs at
`v1.4/controls/Cxx-*.md`. Do not edit chapter prose directly for those
sections - edit the control specs and let the chapters pull from them. (The
pull mechanism is wired in Phase 2; in this scaffold the chapters are stubs.)

## Layout

```
_quarto.yml              Book config: formats, chapters, crossref, bibliography
chapters/                Chapter and appendix sources (00-cover ... A3-references)
assets/images/           Logos, cover art, architecture diagrams
assets/diagrams/         Mermaid source where kept separately
assets/fonts/            Custom fonts, if any
references.bib           Bibliography database (content lands Phase 4)
harvard.csl              Harvard citation style (Cite Them Right 12th edition)
```

## Licensing

- Code (build config, scripts): MIT - see `LICENSE-MIT`.
- Content (the paper text, figures): Creative Commons Attribution 4.0
  International (CC BY 4.0) - see `LICENSE-CC-BY-4.0`.

## Status

Phase 1 scaffold: an empty book that builds cleanly to PDF and HTML, with
cross-references, Mermaid, and code highlighting verified. Content migration
is Phase 2; v1.4 deltas are Phase 3; polish and release are Phase 4.
