# DRIFT-FINDINGS - Phase 2 control source-of-truth refactor

Captured during Phase 2 content migration. These are surfaced for triage, not
reconciled. Do not act on them silently.

## Summary

The Part D refactor ("render control chapters from on-disk specs") completed for
C20 only. C01-C19 could not be put on the include pattern because format-
compatible on-disk specs for them do not exist. Details below.

## Finding 1 (structural) - paper-form specs for C01-C19 are absent on disk

The mandate assumed `v1.4/controls/Cxx-*.md` holds paper-ready control specs for
all controls, sourced from the T1520 baseline. That is true for **C20 only**.
`v1.4/controls/` contains exactly one file: `C20-output-validation.md`.

The full C01-C20 set that does exist on disk is the T1520 **gate-knowledge**
collection at
`v1.4/snapshots/GATE-v1.4-snapshot-2026-06-26T1520/v1.4/workstream-9/gate-knowledge/controls/Cxx.md`.
Those files are a different artifact from the paper's control entries:

- They carry YAML front matter (`type`, `control_id`, `layer`, `tags`,
  `depends_on`, `distinct_from`, `source_of_truth`).
- Their body is structured as `## Mechanism`, `## Relationships`,
  `## Implementation notes`, `## Evidence required` - a knowledge-base article.
- The paper's control entries are structured as Why / What / How / Evidence /
  Failure Modes.
- They contain absolute internal links (`/controls/C04.md`,
  `/abom-templates/...`) that do not resolve inside the paper.

They are therefore not "the same content modulo formatting" (mandate case a) and
not a missing spec (case c) in the literal sense - they are a parallel
representation. Including them raw would inject YAML front matter and a different
section structure into the paper.

**Resolution used:** C01-C19 remain inlined in the layer chapters from the
frozen-Doc migration (faithful to the frozen Doc). No reformatting was done.

**Recommended resolution (future session):** promote paper-form specs into the
repo at `controls/Cxx-*.md` - either by extracting each control's migrated
catalog entry from the chapter, or by reformatting the gate-knowledge specs into
Why/What/How/Evidence/Failure-Modes form - then reconcile the two representations
control by control, then switch each chapter section to an include via the
`chapters/_includes/` wrapper pattern already established for C20.

## Finding 2 (expected drift to check during Finding 1 resolution)

When paper-form specs are created and reconciled against the gate-knowledge
specs, the following controls are where divergence is expected (per the frozen
Doc's own "Changes since v1.2.8" changelog and the Phase 2 context discipline).
These are not yet verified line by line; they are flagged so the future
reconciliation knows where to look.

- **C17, C18, C19** - added in v1.3. Both representations exist; confirm the
  paper entry and the gate-knowledge spec agree on mechanism and evidence.
- **C04** - gained a `Discovered` lifecycle state to receive C17 candidates.
- **C08** - gained a Failure-Modes cross-reference to C18 and a Memory-flow
  scope note.
- **C10** - gained one clarifying sentence on Determinism scope.

## C20 - no drift

C20 is rendered directly from `controls/C20-output-validation.md`, which is the
corrected T1520 spec (six-framework alignment: NIST AI RMF, ISO/IEC 42001, OWASP
AISVS, MITRE ATLAS, NIST SSDF, EU AI Act). It is the source of truth, so there is
nothing to diverge from. Headings were demoted two levels (`#` to `###`, `##` to
`####`) so the control nests under the Layer 3 chapter; content is unchanged.
