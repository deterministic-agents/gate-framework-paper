# GATE Framework Paper

Source for the *Governed Agent Trust Environment* (GATE) framework paper,
version 1.4. Built with [Quarto](https://quarto.org) as a book that renders to
both PDF and HTML from a single markdown source of truth.

## Build

```
quarto render
```

Outputs:

- HTML book: `_book/index.html`
- PDF book:  `_book/GATE-v1.4.pdf`

Render a single format with `quarto render --to html` or `--to pdf`.

## Layout

```
_quarto.yml          Book config: formats, chapters, crossref, bibliography
index.qmd            Cover / home page (title, license, hero image)
chapters/            Chapter and appendix sources, in reading order
chapters/_includes/  Thin wrappers that include on-disk control specs
controls/            Source-of-truth control specs included by the paper
assets/images/       Hero and figures (see assets/images/README.md)
references.bib       Bibliography database (content lands Phase 4)
harvard.csl          Harvard citation style (Cite Them Right 12th edition)
```

The chapter set mirrors the v1.4 paper's section structure 1:1 (front matter,
sixteen body chapters, seven appendices). Control catalog chapters 11-14 carry
the four layers.

## Source authority for control sections

A control whose canonical spec lives in `controls/Cxx-*.md` is rendered into its
layer chapter through a wrapper in `chapters/_includes/`. Edit the spec, not the
chapter prose, for those sections. As of Phase 2 this applies to **C20** only;
C01-C19 are inlined from the frozen-Doc migration because paper-form specs for
them do not yet exist on disk. See `DRIFT-FINDINGS.md`.

## Licensing

- Code (build config): MIT - see `LICENSE-MIT`.
- Content (paper text, figures): CC BY 4.0 - see `LICENSE-CC-BY-4.0`.

## Status

Phase 2 (content migration) complete: the v1.4 paper content is migrated from
the frozen Doc and builds to PDF and HTML. Phase 3 applies the pending paper
updates (pu06-pu10, count normalisations, version sweep); Phase 4 is brand,
typography, and bibliography.
