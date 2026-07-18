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

## v1.4 fix pass (2026-07-04)

The v1.4 fix pass restored missing content, applied the staged paper-updates 06,
07, 08, and 10, and rewrote the reference repository chapter for the v1.4 release
posture. Executed in HTML-first mode; PDF-only concerns skipped.

**Restored from v1.3 docx (Table extraction via python-docx):**

- 4.2 Principle Evidence Reference Table - 8 rows restored; extended for the
  v1.4 defence-in-depth and evidence-first entries to name C20.
- 6.3 Component Responsibilities Table - 16 rows restored, extended with
  Discovery Service (C17), Assurance Plane (C19), Output Classifier (C20).
- Chapter 7 Controls at a Glance - restored the full 20-row control summary
  table with Layer, Boundary, Enforces, and Produces-Evidence columns.
- 15.5 Minimum Controls by Tool Category - 5-row table (read_only, reversible,
  irreversible, financial, infrastructure) restored with C17, C18, C19, C20
  entries added per category.
- Appendix B.1 NIST AI RMF and B.2 ISO/IEC 42001 - 20-row mapping tables
  restored; C20 rows added per the v1.4 six-framework alignment.

**Staged updates applied:**

- Update 06 (Standard Mappings appendix): B.3 AISVS, B.4 ATLAS, B.5 SSDF
  entries added after the ISO section. B.1 and B.2 preambles updated to mention
  C20.
- Update 07 finish: Phase 2 and Phase 3 exit criteria extended with the C20
  entries. Phase 3 add-list now carries the C20 enforce-mode promotion.
- Update 08 Part A (control count): "16 Core Controls" and "19 controls" swept
  to "20 Core Controls" and "20 controls" respectively. "C01-C16" in scope
  chapter reworded to "the enrolment-dependent controls".
- Update 08 Part B (conformance section): Check17 and Check18 reclassified as
  PARTIAL-or-AUTOMATED conditional on bundle-store URI configuration. Check20
  paragraph added as PARTIAL. Conformance totals line added: 9 AUTOMATED / 11
  PARTIAL default; 11 / 9 with both URIs configured. C20 reporting metrics
  added to the Suggested Conformance Reporting list.
- Update 10 (changelog v1.4 entry): inserted as the leading "Changes since v1.3"
  section; existing "Changes since v1.2.8" preserved as the v1.3 entry below.
  Known Issues / deferred to v1.5 section included at the same heading level
  as Added / Changed / Deprecated.

**Rendering artifacts and prose fixes:**

- ERRATA leak in `controls/C20-output-validation.md` line 203 removed; the
  correct event-type and retention-class prose stands alone with no editorial
  annotation.
- `**` artifacts in chapters 6 and 7 (Phase 1 / 2 / 3 headers, Implementation
  note) rewritten as proper H3 headings and inline emphasis.
- C20's local References subsection removed; EU AI Act, OWASP AISVS, MITRE
  ATLAS, NIST SSDF, and OKF citations consolidated in the main References
  chapter with Harvard entries.

**Roadmap items added (Part 3 of the fix prompt):**

- Chapter 10 rewritten: release-status callout aligned to v1.4; runner status
  reflects 9-of-20 automated (11-of-20 when configured); gate-rust,
  gate-fuzz, and gate-knowledge added to the repository inventory with scope
  paragraphs and cross-language guarantee prose.
- C16 (chapter 14): MITRE ATLAS alignment subsection added with in-scope
  technique families, out-of-scope families, and the pointer to
  `gate-conformance/mappings/mitre-atlas.yaml`.
- Appendix A2: "Cross-framework mappings tracked outside the paper" pointer
  added so operators seeking EU AI Act, DORA, or HIPAA can find the
  gate-conformance mappings directory. Note: DORA and HIPAA mappings are not
  yet published as separate YAML files; the pointer names the tracking
  location, not a published artefact. Flag to Andrew if the intent is to
  publish these before v1.4 goes live.

**Deferred (proposals, awaiting sign-off):**

- Paper update 13 - Framework improvement proposals: fail-closed matrix gaps
  (chapter 15.1), glossary debt (Appendix F), executive-summary boundary
  model framing, and the output-boundary scope statement (last one already
  applied in the scope chapter as part of the fix pass). Draft at
  `v1.4/paper-updates/13-framework-improvement-proposals.md`.

**Style sweep after the fix pass:**

- 0 em dashes across `chapters/`, `controls/`, and `index.qmd`.
- 0 `**` artifacts remaining outside inline emphasis.
- 0 `ERRATA` / `Insertion point` markers.
- References chapter contains NIST, ISO/IEC 42001, EU AI Act, OWASP AISVS,
  MITRE ATLAS, NIST SSDF, and Google Cloud (OKF) entries in Harvard form.

Verification against the v1.4 prompt's Part 5 checklist is at the tail of the
review report handed back with this fix pass.
