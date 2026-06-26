# Control includes

Source-of-truth pattern for control sections in the paper.

Each control whose canonical spec lives on disk at `/controls/Cxx-*.md` is
rendered into its layer chapter through a thin wrapper here. The wrapper does
nothing but `{{< include >}}` the on-disk spec, so the spec is the single place
to edit that control. Edit `/controls/Cxx-*.md`, never the chapter prose, for
those sections.

## Current state (Phase 2)

- `C20.qmd` -> includes `/controls/C20-output-validation.md` (the corrected
  T1520 spec with six-framework alignment). Rendered into
  `13-control-catalog-layer-3.qmd`.

C01-C19 are not yet on this pattern. Their paper-form specs do not exist on
disk: the only on-disk specs (the T1520 `gate-knowledge` set) are a different
artifact (KB articles with YAML front matter and Mechanism/Relationships
structure), not format-compatible with the paper's Why/What/How/Evidence/Failure
-Modes control entries. Those controls remain inlined in the layer chapters from
the frozen-Doc migration. See `../../DRIFT-FINDINGS.md`.

## Heading levels

Specs are stored at the heading depth they appear in the catalog: a control is
`### Control NN - Title {#sec-cNN}`, its sub-sections are `####`. This lets the
include nest correctly under the `# Layer N` chapter heading.
